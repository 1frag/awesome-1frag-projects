import aiohttp.web
import aiohttp_jinja2
import jinja2
import json
import os
import random
import datetime

db = []  # ha-ha
RULE = {
    'x': lambda a, b: a * b,
    '/': lambda a, b: a / b,
}


@aiohttp_jinja2.template('index.html')
async def main(request: aiohttp.web.Request):
    for_first = [3, 4]
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

    db.append({
        'first': first,
        'op': op,
        'second': second,
        'answer': answer,
        'res': res,
        'created_at': datetime.datetime.now(),
    })
    return aiohttp.web.Response(body=str(int(res)))


@aiohttp_jinja2.template('stats.html')
async def stats(request: aiohttp.web.Request):
    return {'db': [{
        'i': j,
        'exc': str(i['first']) + i['op'] + str(i['second']),
        'cor': RULE[i['op']](i['first'], i['second']),
        'wrote': i['answer'],
        'correct': 'success' if i['res'] else 'danger',
    } for j, i in enumerate(db)]}


async def clear_stats(request: aiohttp.web.Request):
    global db
    db = []
    return aiohttp.web.Response(body='Ok')


if __name__ == '__main__':
    app = aiohttp.web.Application()
    app.add_routes([
        aiohttp.web.get('/', main),
        aiohttp.web.post('/send_answer', send_answer),
        aiohttp.web.get('/stats', stats),
        aiohttp.web.post('/clear', clear_stats),
    ])
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader('./templates'),
    )
    aiohttp.web.run_app(app, port=os.getenv('PORT', 9090))
