import aiohttp.web
import aiohttp_jinja2
import jinja2
import os
import pathlib

from .math_tester import MathTesterApp
from .simplest import routes
from .sudoku import SudokuApp
from .clipboard_sharing import CSApp
try:
    from ya_fetcher.web import FetcherApp
except ImportError:
    FetcherApp = aiohttp.web.Application


if __name__ == '__main__':
    super_app = aiohttp.web.Application()
    aiohttp_jinja2.setup(
        super_app, loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / 'templates'),
    )

    super_app.add_subapp('/math-tester', MathTesterApp())
    super_app.add_subapp('/sudoku-solver', SudokuApp())
    super_app.add_subapp('/fetcher', FetcherApp())
    super_app.add_subapp('/clipboard_sharing', CSApp())
    super_app.add_routes(routes)

    aiohttp.web.run_app(super_app, port=os.getenv('PORT', 9090))
