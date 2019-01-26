# 文章相关 PRC调用
import typing

from apistellar.helper import register
from aiohttp import ClientSession, FormData
from apistellar.helper import RestfulApi


class Article(RestfulApi):
    # 这个url会被连接上域名和注册的endpoint之后注入到方法中使用。
    url = None  # type: str
    session = None  # type: ClientSession

    @register("/import", conn_timeout=10)
    async def import_(self, cookies: dict=None):
        resp = await self.session.get(self.url)
        return await resp.read()

    @register("/check", conn_timeout=10)
    async def check(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.read()

    @register("/load", "data", error_check=lambda x: x["code"] != 0, conn_timeout=10)
    async def load(self, username: str, password: str, cookies: dict=None):
        params = dict()
        if username is not None:
            params["username"] = username
        if password is not None:
            params["password"] = password
        resp = await self.session.get(self.url, params=params)
        return await resp.json()

    @register("/upload", conn_timeout=10)
    async def upload(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.read()

    @register("/export", conn_timeout=10)
    async def export(self, ids: str, code: str=None, cookies: dict=None):
        params = dict()
        if ids is not None:
            params["ids"] = ids
        if code is not None:
            params["code"] = code
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

    @register("/modify", "data", error_check=lambda x: x["code"] != 0, conn_timeout=10)
    async def modify(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.json()

    @register("/edit", conn_timeout=10)
    async def edit(self, id: str, cookies: dict=None):
        params = dict()
        if id is not None:
            params["id"] = id
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

    @register("/update", conn_timeout=10)
    async def update(self, form_fields: typing.List[dict], cookies: dict=None):
        data = FormData()
        for meta in form_fields:
            data.add_field(meta["name"],
                           meta["value"],
                           filename=meta.get("filename"),
                           content_type=meta.get("content_type"))
        resp = await self.session.post(self.url, data=data)
        return await resp.read()

    @register("/delete", conn_timeout=10)
    async def delete(self, id: str, cookies: dict=None):
        params = dict()
        if id is not None:
            params["id"] = id
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

    @register("/article", conn_timeout=10)
    async def article(self, id: str, cookies: dict=None):
        params = dict()
        if id is not None:
            params["id"] = id
        resp = await self.session.get(self.url, params=params)
        return await resp.json()

    @register("/me", conn_timeout=10)
    async def me(self, code: str, cookies: dict=None):
        params = dict()
        if code is not None:
            params["code"] = code
        resp = await self.session.get(self.url, params=params)
        return await resp.json()

    @register("/contact", conn_timeout=10)
    async def contact(self, cookies: dict=None):
        resp = await self.session.get(self.url)
        return await resp.json()

    @register("/show", conn_timeout=10)
    async def show(self, searchField: str=None, fulltext: bool=None, _from: int=None, size: int=None, cookies: dict=None):
        params = dict()
        if searchField is not None:
            params["searchField"] = searchField
        if fulltext is not None:
            params["fulltext"] = fulltext
        if _from is not None:
            params["_from"] = _from
        if size is not None:
            params["size"] = size
        resp = await self.session.get(self.url, params=params)
        return await resp.json()

    @register("/cut", conn_timeout=10)
    async def cut(self, url: str, top: int=None, left: int=None, width: int=None, height: int=None, cookies: dict=None):
        params = dict()
        if url is not None:
            params["url"] = url
        if top is not None:
            params["top"] = top
        if left is not None:
            params["left"] = left
        if width is not None:
            params["width"] = width
        if height is not None:
            params["height"] = height
        resp = await self.session.get(self.url, params=params)
        return await resp.read()

