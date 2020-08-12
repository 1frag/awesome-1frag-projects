import aiohttp.web
import aiohttp_jinja2
import jinja2
import json
import os
import random
import time
import datetime
import aiopg.sa
import typing
import base64
from bs4 import BeautifulSoup
from aiomisc import timeout, threaded

from cpp_extend import sudoku

db: typing.Optional[aiopg.sa.engine.Engine] = None
RULE = {
    'x': lambda a, b: a * b,
    '/': lambda a, b: a / b,
}
DIGEST = None


@aiohttp_jinja2.template('index.html')
async def main(request: aiohttp.web.Request):
    for_first = [2, 3, 4, 5, 6]
    for_second = list(range(2, 11))
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


async def database(_):
    global db
    config = {'dsn': os.getenv('DATABASE_URL') or input('db dsn: ')}
    db = await aiopg.sa.create_engine(**config)
    yield
    db.close()
    await db.wait_closed()


async def callback(request):
    data = await request.read()
    headers = request.headers
    print(f'Request#{id(request)}:\n{data=}\n{headers=}\n{request.rel_url}\n')
    return aiohttp.web.Response(status=200, text='')


# sudoku part
class Mock:
    attrs = {'d': None}


def init():
    global DIGEST
    with open('./digest.json') as f:
        DIGEST = json.load(f)


def parse_field(pure_html):
    get_path = lambda e: e.find('div', class_='cell-value').find('path')
    get_num = lambda e: DIGEST.get((get_path(e) or Mock()).attrs['d'])
    soup = BeautifulSoup(pure_html, 'html.parser')
    f = [get_num(e) for e in soup.find_all('td')]
    return [list(k) for k in zip(*[iter(f)]*9)]


''' Slow realization on Python. Now using c++ sudoku extention to solve problems
def check(field):
    _check = lambda q: len(r:=[t for t in q if t]) == len(set(r))
    # row
    for row in field:
        if not _check(row):
            return False
    # column
    for i in range(9):
        if not _check([e[i] for e in field]):
            return False
    # cube
    for i in range(3):
        for j in range(3):
            p = [r[3*j:3+3*j] for r in field[3*i:3+3*i]]
            if not _check(p[0] + p[1] + p[2]):
                return False
    return True


@timeout(45)  # sec
async def solve(field_):
    @threaded
    def _solve(field):
        def wrapper(i, j):
            if i == 9 and j == 0:
                return True
            next_i, next_j = (i + 1, 0) if (j == 8) else (i, j + 1)
            if field[i][j] is not None:
                return wrapper(next_i, next_j)
            for k in range(1, 10):
                field[i][j] = str(k)
                if check(field) and wrapper(next_i, next_j):
                    return True
            field[i][j] = None
            return False
        return wrapper(0, 0)
    await _solve(field_)
    return field_
'''


async def solve(field_):
    return sudoku.solve(field_)


def pretty_print(field):
    def it_():
        for row in field:
            for e in row:
                yield e or '.'
    it = it_()
    def get_three():
        return ' '.join([next(it) for _ in range(3)])
    for i in range(3):
        for _ in range(3):
            print(get_three(), '|', get_three(), '|', get_three())
        if i != 2:
            print('-' * (9 + 2 + 2 * 5))


async def sudoku_handler(request):
    start_at = time.time()
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        field = parse_field(msg.data)
        print('New query:'); pretty_print(field)
        print(base64.encodebytes(json.dumps(field).encode()).decode())
        try:
            if field := await solve(field):
                await ws.send_json(field)
                print('Result:'); pretty_print(field)
            else:
                await ws.send_json(dict(result=False))
                print('Result not found')
        except TimeoutError:
            await ws.send_json(dict(result=False))
            print('Timeout request')
        print(f'at {time.time() - start_at} sec')
        await ws.close()


if __name__ == '__main__':
    init()
    app = aiohttp.web.Application()
    app.cleanup_ctx.append(database)
    app.add_routes([
        aiohttp.web.get('/', main),
        aiohttp.web.post('/send_answer', send_answer),
        aiohttp.web.get('/stats', stats),
        aiohttp.web.route('*', '/callback', callback),
        aiohttp.web.get('/sudoku-solver', sudoku_handler),
    ])
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader('./templates'),
    )
    aiohttp.web.run_app(app, port=os.getenv('PORT', 9090))

