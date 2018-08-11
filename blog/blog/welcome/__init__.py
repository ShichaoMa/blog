import os
import asyncio
import aiofiles

from apistar import App
from apistar.http import QueryParam, RequestData, Path

from star_builder import Controller, route, get, post, require, Session
from toolkit.settings import FrozenSettings

from ..utils import project_path
from ..components import FormParam

from star_builder.bases.components import FileStream

from star_builder.route import websocket


@route("/", name="welcome")
class WelcomeController(Controller):

    @get("/")
    def index(app: App, path: QueryParam, settings: FrozenSettings):
        return app.render_template(
            'index.html',
            author=settings.AUTHOR,
            _path=path or "",
            page_size=settings.PAGE_SIZE, url_for=app.reverse_url)

    # @post("/upload_image")
    # @require(Session, judge=lambda x: x.get("login"))
    # def upload(file: FormParam):
    #     file.save(os.path.join(project_path, "static/img", file.filename))
    #     return {"success": True}
    #
    # @post("/test_upload")
    # async def up(stream: FileStream):
    #     import ipdb;ipdb.set_trace()
    #     async for file in stream:
    #         if file.filename:
    #             with open(file.filename, "wb") as f:
    #                 async for chuck in file:
    #                     f.write(chuck)
    #         else:
    #             # 没有filename的是其它类型的form参数
    #             arg = await file.read()
    #             print(f"Form参数：{file.name}={arg.decode()}")
    #
    # @get("/test_download")
    # async def down(filename: str):
    #     import ipdb;ipdb.set_trace()
    #     f = await aiofiles.open(filename, "rb")
    #     from star_builder.bases.response import FileResponse
    #     return FileResponse(f, filename=filename, headers={"Content-Length": os.path.getsize(filename)})
    #
    # @websocket("/test/websocket")
    # async def receive(message, path: Path):
    #     _text = message.get("text")
    #     print("received", _text, f"from {path}")
    #     return {"success": "ok"}
    #
    # @websocket("/test/websocket1")
    # class Handler(object):
    #     def __init__(self, send):
    #         self.send = send
    #         self.message = ""
    #
    #     async def websocket_connect(self, message, path: Path):
    #         print(f"Websocket of {path} connect. ")
    #         return {"success": "ok"}
    #
    #     async def websocket_disconnect(self, message, path: Path):
    #         print("Got total data: %s" % self.message)
    #         print(f"Websocket of {path} disconnect. ")
    #
    #     async def websocket_receive(self, message):
    #         text = message.get("text")
    #         self.message += text
    #         await self.send(f"got piece: {text}")
    #         await asyncio.sleep(1)
    #         return {"success": "ok"}
