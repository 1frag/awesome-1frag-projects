import itertools
import json
import logging
import pathlib
import time

import aiohttp.web

from bs4 import BeautifulSoup

from . import solver


logging.basicConfig(level=logging.DEBUG)

DIGEST: dict
try:
    with open(pathlib.Path(__file__).parent / 'digest.json') as _digest:
        DIGEST = json.load(_digest)
except (IOError, json.JSONDecodeError) as e:
    raise ImportError(f'digest.json not found.')


class SudokuApp(aiohttp.web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_routes([
            aiohttp.web.get('/', sudoku_handler),
        ])


def parse_field(pure_html):
    def inner():
        for td in BeautifulSoup(pure_html, "html.parser").find_all("td"):
            path = td.find('div', class_='cell-value').find('path')
            if path is None:
                yield 0
            else:
                yield DIGEST[path.attrs['d']]

    return [*map(list, zip(*[inner()] * 9))]


def pretty_print(field: list[list[int]]) -> str:
    it = map(lambda x: str(x or "."), itertools.chain(*field))
    by_3 = map(" ".join, zip(*[it] * 3))
    by_9 = map(" | ".join, zip(*[by_3] * 3))
    total = map('\n'.join, zip(*[by_9] * 3))
    return ("\n" + "+".join(map("-".__mul__, (6, 7, 6))) + "\n").join(total)


async def sudoku_handler(request):
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        task = parse_field(msg.data)
        logging.debug('New query:\n%s', pretty_print(task))
        start_at = time.time()
        solution = next(solver.solve_sudoku(task))
        logging.debug('Result:\n%s\nin %s seconds', pretty_print(solution),
                      time.time() - start_at)
        await ws.send_json(solution)
        await ws.close()
