import os
import typing

from apistar import App, http
from apistar.http import QueryParam

from apistellar import Controller, route, get, post, require, Session, \
    FormParam, SettingsMixin, MultiPartForm
from apistellar.helper import return_wrapped

from blog.blog.utils import project_path
from blog.blog.article.article import Article


@route("/", name="welcome")
class WelcomeController(Controller, SettingsMixin):
    """
    欢迎页
    """
    @get("/")
    def index(self, app: App, path: QueryParam) -> str:
        """
        首页
        :param app:
        :param path: 子路径
        :ex path:
        `"/article?a=3"`
        :param settings: 配置信息
        :return:
        ```html
        <html>...</html>
        ```
        """
        return app.render_template(
            'index.html',
            author=self.settings["AUTHOR"],
            _path=path or "",
            page_size=self.settings["PAGE_SIZE"],
            url_for=app.reverse_url,
            code_swatch=str(self.settings.get_bool("NEED_CODE")).lower())

    @post("/upload_image")
    @require(Session, judge=lambda x: x.get("login"))
    def upload(self, files: MultiPartForm):
        for name, file in files.items():
            file.save(os.path.join(project_path, "static/img", file.filename))
        return {"success": True}

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
        return [data]

