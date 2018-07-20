import os
from apistar import App
from apistar.http import QueryParam, RequestData

from star_builder import Controller, route, get, post, require, Session
from toolkit.settings import FrozenSettings

from ..utils import project_path
from ..components import FormParam


@route("/", name="welcome")
class WelcomeController(Controller):

    @get("/")
    def index(app: App, path: QueryParam, settings: FrozenSettings):
        return app.render_template(
            'index.html',
            author=settings.AUTHOR,
            _path=path or "",
            page_size=settings.PAGE_SIZE, url_for=app.reverse_url)

    @post("/upload_image")
    @require(Session, judge=lambda x: x.get("login"))
    def upload(file: FormParam):
        file.save(os.path.join(project_path, "static/img", file.filename))
        return {"success": True}
