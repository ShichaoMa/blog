import os
import typing

from apistar import App, http
from apistar.http import QueryParam

from apistellar import Controller, route, get, post, require, Session, \
    FormParam, SettingsMixin, MultiPartForm, FileStream
from apistellar.helper import return_wrapped

from blog.utils import project_path
from blog.article.article import Article


@route("/", name="welcome")
class WelcomeController(Controller, SettingsMixin):
    """
    欢迎页
    """
    @get("/")
    def index(self, app: App, path: QueryParam=None) -> str:
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
