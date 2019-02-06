import os

from apistar import App
from apistar.http import QueryParam

from apistellar import Controller, route, get, post, require, Session, \
    settings, MultiPartForm


@route("/", name="welcome")
class WelcomeController(Controller):
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
            author=settings["AUTHOR"],
            _path=path or "",
            page_size=settings["PAGE_SIZE"],
            url_for=app.reverse_url,
            code_swatch=str(settings.get_bool("NEED_CODE")).lower())

    @post("/upload_image")
    @require(Session, judge=lambda x: x.get("login"))
    def upload(self, files: MultiPartForm):
        for name, file in files.items():
            file.save(os.path.join(
                settings["PROJECT_PATH"], "static/img", file.filename))
        return {"success": True}

    @post("/a/{b}/{+path}")
    async def test(self, b: int, path: str):
        print(b, path)
