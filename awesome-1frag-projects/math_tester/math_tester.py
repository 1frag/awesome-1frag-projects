import asyncio
import aiohttp.web
import aiohttp_jinja2
import json
import os
import random
import aiopg.sa
import typing

__all__ = 'MathTesterApp',

db: typing.Optional[aiopg.sa.engine.Engine] = None
RULE = {
    'x': lambda a, b: a * b,
    '/': lambda a, b: a / b,
}

_m, _ = os.path.split(__file__)
with open(_m + '/../static/upload/settings.json') as f:
    SETTINGS = json.load(f)


class MathTesterApp(aiohttp.web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_ctx.append(database)
        self.add_routes([
            aiohttp.web.get('/', main),
            aiohttp.web.post('/send_answer', send_answer),
            aiohttp.web.get('/stats', stats),
            aiohttp.web.get('/refresh', refresh_settings)
        ])


@aiohttp_jinja2.template('index.html')
async def main(request: aiohttp.web.Request):
    for_first = SETTINGS['math-tester']['for-first']
    for_second = SETTINGS['math-tester']['for-second']
    for_op = ['x', '/']

    first = random.choice(for_first)
    second = random.choice(for_second)
    op = random.choice(for_op)
    answer = first * second

    if op == 'x':
        if random.randint(0, 1) == 1:
            first, second = second, first
    else:
        if random.randint(0, 1) == 1:
            first, second = answer, first
        else:
            first, second = answer, second

    return {
        'first': first, 'second': second, 'op': op,
    }


async def send_answer(request: aiohttp.web.Request):
    try:
        data: dict = await request.json()
        first, op, second, answer = map(
            data.__getitem__,
            ('first', 'op', 'second', 'answer')
        )
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

    async with db.acquire() as conn:
        conn: aiopg.sa.SAConnection
        await conn.execute('''
            insert into app_answer (first, op, second, answer, res)
            values (%s, %s, %s, %s, %s)
        ''', (first, op, second, answer, res))
    return aiohttp.web.Response(body=str(int(res)))


@aiohttp_jinja2.template('stats.html')
async def stats(request: aiohttp.web.Request):
    async with db.acquire() as conn:
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


async def refresh_settings(request):
    await asyncio.sleep(10)
    global SETTINGS
    async with aiohttp.ClientSession() as sess:
        async with sess.get(f'http://0.0.0.0:{os.getenv("PORT", 9090)}/static/upload/settings.json') as resp:
            SETTINGS = await resp.json()
    return aiohttp.web.json_response(SETTINGS)


async def database(_):
    global db

    def get_dsn():
        if dsn := os.getenv('DATABASE_URL'):
            return dsn
        try:
            return json.loads(os.popen('heroku config -j').read())['DATABASE_URL']
        except Exception:
            pass
        return input('db dsn: ')

    config = {'dsn': get_dsn()}
    db = await aiopg.sa.create_engine(**config)
    yield
    db.close()
    await db.wait_closed()
