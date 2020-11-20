import aiohttp.web
import os


async def callback_handler(request):
    data = await request.read()
    headers = request.headers
    print(f'Request#{id(request)}:\n{data=}\n{headers=}\n{request.rel_url}\n')
    return aiohttp.web.Response(status=200, text='')


async def upload_handler(request):
    if not (name := request.query['name']):
        raise aiohttp.web.Response(status=400)
    path = f'/static/upload/{name}'
    if (method := request.method) == 'POST':
        reader = await request.multipart()
        with open(_m + path, 'wb') as fl:
            while not reader.at_eof():
                bdrd = await reader.next()
                while bdrd and not bdrd.at_eof():
                    fl.write(await bdrd.read())
        return aiohttp.web.Response(status=201)
    elif method == 'DELETE':
        os.remove(path)
        return aiohttp.web.Response(status=204)
    return aiohttp.web.Response(status=405)


_m, _ = os.path.split(__file__)
routes = [
    aiohttp.web.route('*', '/', callback_handler),
    aiohttp.web.route('*', '/upload', upload_handler),
    aiohttp.web.static('/static', _m + '/static'),
]
