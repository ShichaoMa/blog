from apistar import App
from apistar.http import QueryParam

from star_builder import Controller, route, get, post
from toolkit.settings import FrozenSettings


@route("/", name="welcome")
class WelcomeController(Controller):

    @get("/")
    def index(app: App, path: QueryParam, settings: FrozenSettings):
        return app.render_template(
            'index.html',
            author=settings.AUTHOR,
            _path=path or "",
            page_size=settings.PAGE_SIZE, url_for=app.reverse_url)
