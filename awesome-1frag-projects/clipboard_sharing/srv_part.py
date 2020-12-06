import aiohttp.web
import aiohttp.http_websocket
import asyncio
import janus
import collections

MsgType = aiohttp.http_websocket.WSMessage


class CSApp(aiohttp.web.Application):
    class Request(aiohttp.web.Request):
        app: 'CSApp'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_routes([
            aiohttp.web.get(r'/start/{code:\w+}', ws_handler),
        ])
        self.watchers: dict[str, list[janus.Queue]] = collections.defaultdict(list)

    def listen(self, code: str, queue: janus.Queue):
        self.watchers[code].append(queue)
        print(self.watchers)

    async def send(self, code: str, msg: MsgType, ignore_queue=None):
        for each in self.watchers[code]:
            if each is ignore_queue:
                continue
            await each.async_q.put(MsgType(data=msg.data, type='ws', extra=msg.extra))


async def ws_handler(request: 'CSApp.Request'):
    code: str = request.match_info['code']
    queue: janus.Queue[MsgType] = janus.Queue()
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    request.app.listen(code, queue)

    async def fetch():
        async for msg in ws:  # type: MsgType
            print(msg, msg.__class__)
            await queue.async_q.put(msg)

    asyncio.ensure_future(fetch())
    while True:
        cur_msg = await queue.async_q.get()
        if cur_msg.type == aiohttp.http_websocket.WSCloseCode:
            break
        if cur_msg.type == aiohttp.http_websocket.WSMsgType.TEXT:
            await request.app.send(code, cur_msg, queue)
        if cur_msg.type == 'ws':
            await ws.send_str(cur_msg.data)
    return ws
