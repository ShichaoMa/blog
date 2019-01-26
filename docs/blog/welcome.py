# 欢迎页 PRC调用
import typing

from apistellar.helper import register
from aiohttp import ClientSession, FormData
from apistellar.helper import RestfulApi


class Welcome(RestfulApi):
    # 这个url会被连接上域名和注册的endpoint之后注入到方法中使用。
    url = None  # type: str
    session = None  # type: ClientSession

    @register("/", conn_timeout=10)
    async def index(self, path: str=None, cookies: dict=None):
        params = dict()
        if path is not None:
            params["path"] = path
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

    @register("/upload_image", conn_timeout=10)
    async def upload_image(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.read()

    @register("/a/{b}/{+path}", conn_timeout=10, have_path_param=True)
    async def a_b_path(self, path_params: dict, cookies: dict=None):
        resp = await self.session.post(self.url)
        return await resp.read()

