import asyncio
import aiohttp.web
import aiohttp_jinja2
import json
import os
import random
import aiopg.sa
import typing
import operator

__all__ = 'MathTesterApp',

db: typing.Optional[aiopg.sa.engine.Engine] = None
RULE = {'x': operator.mul, '/': operator.floordiv}


class MathTesterApp(aiohttp.web.Application):
    class Request(aiohttp.web.Request):
        app: 'MathTesterApp'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {}
        self.db: typing.Optional[aiopg.sa.engine.Engine] = None
        self.cleanup_ctx.append(self.database)
        self.add_routes([
            aiohttp.web.get('/', main),
            aiohttp.web.post('/send_answer', send_answer),
            aiohttp.web.get('/stats', stats),
        ])

    @staticmethod
    def _get_db_dsn():
        if dsn := os.getenv('DATABASE_URL'):
            return dsn
        try:
            return json.loads(os.popen('heroku config -j').read())['DATABASE_URL']
        except Exception:
            return input('db dsn: ')

    async def settings_updater(self):
        while True:
            async with self.db.acquire() as conn:  # type: aiopg.sa.connection.SAConnection
                res = await conn.execute("select key, value from app_settings where key like 'mt_%%'")
                self.settings |= {row['key']: json.loads(row['value']) for row in await res.fetchall()}
            await asyncio.sleep(60)

    async def database(self, *_):
        config = {'dsn': self._get_db_dsn()}
        self.db = await aiopg.sa.create_engine(**config)
        settings_updater = asyncio.Task(self.settings_updater())
        yield
        settings_updater.cancel()
        try:
            await settings_updater
        except TimeoutError:
            pass
        db.close()
        await db.wait_closed()


@aiohttp_jinja2.template('mt_index.html')
async def main(request: MathTesterApp.Request):
    for_first = request.app.settings['mt_for_first']
    for_second = request.app.settings['mt_for_second']
    for_op = ['x', '/']

    first = random.choice(for_first)
    second = random.choice(for_second)
    op = for_op[1 if random.randint(0, 100) < 80 else 1]
    answer = first * second

    if op == 'x':
        if random.randint(0, 1) == 1:
            first, second = second, first
    else:
        if random.randint(0, 1) == 1:
            first, second = answer, first
        else:
            first, second = answer, second

    return dict(first=first, second=second, op=op)


async def send_answer(request: MathTesterApp.Request):
    try:
        data: dict = await request.json()
        first, op, second, answer = map(data.__getitem__, ('first', 'op', 'second', 'answer'))
        first, second, answer = map(int, (first, second, answer))
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(e.__class__, e)
        raise aiohttp.web.HTTPBadRequest(body=str(e))

    try:
        print(f'{RULE[op](first, second)=} {answer=}')
        res = RULE[op](first, second) == int(answer)
    except (KeyError, TypeError, ValueError) as e:
        print(e.__class__, e)
        res = False

    async with request.app.db.acquire() as conn:  # type: aiopg.sa.SAConnection
        await conn.execute('''
            insert into app_answer (first, op, second, answer, res)
            values (%s, %s, %s, %s, %s)
        ''', (first, op, second, answer, res))
    return aiohttp.web.Response(body=str(int(res)))


@aiohttp_jinja2.template('mt_stats.html')
async def stats(request: MathTesterApp.Request):
    async with request.app.db.acquire() as conn:
        from_db = await (await conn.execute('''
            select id,
                   created_at::date                     as day,
                   concat(first, ' ', op, ' ', second)  as exc,
                   calc(first, op, second)              as cor,
                   answer                               as wrote,
                   css_class(res)                       as correct
            from app_answer
            order by created_at;
        ''')).fetchall()
        stats_days = await (await conn.execute('''
            select created_at::date as day,
                   sum(res::int)    as good,
                   count(*)         as total
            from app_answer
            group by created_at::date;
        ''')).fetchall()
        stats_days = {x['day']: x for x in stats_days}
    return {'db': from_db, 'stats': stats_days}
