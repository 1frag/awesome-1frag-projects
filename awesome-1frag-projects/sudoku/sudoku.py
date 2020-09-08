import aiohttp.web
import time
import json
import os
from typing import Optional
import base64
from bs4 import BeautifulSoup

import c_sudoku

DIGEST: Optional[dict] = None
_m, _ = os.path.split(__file__)
try:
    with open(_m + '/digest.json') as f:
        DIGEST = json.load(f)
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    raise ImportError(f'digest.json not found. {_m=} {e=}')


class SudokuApp(aiohttp.web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_routes([
            aiohttp.web.get('/', sudoku_handler),
        ])


def parse_field(pure_html):
    class Mock:
        attrs = {'d': None}

    def get_path(e): return e.find('div', class_='cell-value').find('path')

    def get_num(e): return DIGEST.get((get_path(e) or Mock()).attrs['d'])

    soup = BeautifulSoup(pure_html, 'html.parser')
    f = [get_num(e) for e in soup.find_all('td')]
    return [list(k) for k in zip(*[iter(f)] * 9)]


async def solve(field_):
    return c_sudoku.solve(field_)


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
        print('New query:')
        pretty_print(field)
        print(base64.encodebytes(json.dumps(field).encode()).decode())
        try:
            if field := await solve(field):
                await ws.send_json(field)
                print('Result:')
                pretty_print(field)
            else:
                await ws.send_json(dict(result=False))
                print('Result not found')
        except TimeoutError:
            await ws.send_json(dict(result=False))
            print('Timeout request')
        print(f'at {time.time() - start_at} sec')
        await ws.close()
