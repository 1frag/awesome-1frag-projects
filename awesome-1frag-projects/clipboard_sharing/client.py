import os
import aiohttp
import asyncio
import aiohttp.http_websocket
import threading
import janus
import typing
import tempfile

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # NoQA

MsgType = aiohttp.http_websocket.WSMessage
queue: janus.Queue
last: typing.Optional[str] = None


def copy(target):
    with tempfile.NamedTemporaryFile() as buf:
        buf.write(target if isinstance(target, bytes) else target.encode())
        buf.seek(0)
        os.popen(f'cat {buf.name} | xsel -ib').read()


def paste():
    return os.popen('xsel -b').read()


class WriteOnCopy(threading.Thread):
    def __init__(self):
        super().__init__(target=self.target, daemon=True)
        self.clip = Gtk.Clipboard().get(Gdk.SELECTION_CLIPBOARD)

    def target(self):
        self.clip.connect('owner-change', self.callback)
        Gtk.main()

    def callback(self, *_):
        if last == paste():
            return
        queue.sync_q.put(paste())


async def main():
    global queue
    queue = janus.Queue()
    host = input('set host: ') or '192.168.0.104'
    url = f'ws://{host}:8080/start/asd'
    WriteOnCopy().start()

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            async def fetch():
                global last
                async for msg in ws:  # type: MsgType
                    last = msg.data
                    copy(msg.data)

            asyncio.ensure_future(fetch())
            while True:
                pasted = await queue.async_q.get()
                await ws.send_str(pasted)


if __name__ == '__main__':
    asyncio.run(main())
