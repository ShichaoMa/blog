import os
import glob
import typing

from apistar import App, http
from apistar.http import QueryParam, PathParam

from apistellar import Controller, route, get, post, require, Session, FormParam, FileStream
from apistellar.helper import return_wrapped
from toolkit.settings import FrozenSettings

from blog.article.article import Article
from ..utils import project_path


@route("/", name="welcome")
class WelcomeController(Controller):
    """
    欢迎页
    """
    @get("/")
    def index(self, app: App, path: QueryParam, settings: FrozenSettings) -> Article:
        """
        首页
        :param app:
        :param path: 子路径
        :ex path:
        `"/article?a=3"`
        :ex path:
        `"/import"`
        :param settings: 配置信息
        :return:
        ```json
        {"a": [], "b": 1}
        ```
        :return:
        ```python
        abfdsfdsfs
        ```
        """
        return app.render_template(
            'index.html',
            author=settings.AUTHOR,
            _path=path or "",
            page_size=settings.PAGE_SIZE,
            url_for=app.reverse_url,
            code_swatch="true" if settings.get_bool("NEED_CODE") else "false")
    #
    # @post("/upload_image")
    # @require(Session, judge=lambda x: x.get("login"))
    # def upload(self, file: FormParam):
    #     file.save(os.path.join(project_path, "static/img", file.filename))
    #     return {"success": True}
    #
    # @post("/upload_secret")
    # @require(Session, judge=lambda x: x.get("login"))
    # async def upload_secret(self, stream: FileStream):
    #     file_dir = os.path.join(project_path, "static/secret")
    #     os.makedirs(file_dir, exist_ok=True)
    #     async for file in stream:
    #         if file.filename:
    #             with open(os.path.join(
    #                     file_dir, file.filename.replace(" ", "")), "wb") as f:
    #                 async for chuck in file:
    #                     f.write(chuck)
    #     return {"success": True}
    #
    # @get("/list")
    # @require(Session, judge=lambda x: x.get("login"))
    # def list(self):
    #      file_dir = os.path.join(project_path, "static/secret")
    #      html_tmpl = "<html><header><title>我的私货</title></header><body><ul>%s</ul></body></html>"
    #
    #      urls = list()
    #      for file in glob.glob(os.path.join(file_dir, "*")):
    #         urls.append(file.replace(project_path, ""))
    #      html = html_tmpl % "\n".join(f"<li><a href='{url}'>"
    #                                   f"{os.path.basename(url)}</a></li>" for url in urls)
    #      return html

    @post("/a/{+path}")
    @return_wrapped()
    def test(self, path: str, b: http.QueryParams, name: FormParam, data: Article) -> typing.List[Article]:
        """
        测试
        :param path: 传个地址
        :param name: 输入地址
        :ex name: `abcd`
        :param b: 测试QueryParams
        :ex b:
        ```json
        {"a": 1, "b": 2}
        ```
        :param data: post过来的参数集合
        :ex data:
        ```json
        {"a": 1}
        ```
        :ex data:
        ```json
        {"ab": 1}
        ```
        :return:
        ```json
        {"code": 0, "data": {"a": 1}}
        ```
        """
        print(data)

