import os
import glob

from apistar import App
from apistar.http import QueryParam

from apistellar import Controller, route, get, post, require, Session, FormParam, FileStream
from toolkit.settings import FrozenSettings

from ..utils import project_path


@route("/", name="welcome")
class WelcomeController(Controller):

    @get("/")
    def index(self, app: App, path: QueryParam, settings: FrozenSettings):
        return app.render_template(
            'index.html',
            author=settings.AUTHOR,
            _path=path or "",
            page_size=settings.PAGE_SIZE,
            url_for=app.reverse_url,
            code_swatch="true" if settings.get_bool("NEED_CODE") else "false")

    @post("/upload_image")
    @require(Session, judge=lambda x: x.get("login"))
    def upload(self, file: FormParam):
        file.save(os.path.join(project_path, "static/img", file.filename))
        return {"success": True}

    @post("/upload_secret")
    @require(Session, judge=lambda x: x.get("login"))
    async def upload_secret(self, stream: FileStream):
        file_dir = os.path.join(project_path, "static/secret")
        os.makedirs(file_dir, exist_ok=True)
        async for file in stream:
            if file.filename:
                with open(os.path.join(
                        file_dir, file.filename.replace(" ", "")), "wb") as f:
                    async for chuck in file:
                        f.write(chuck)
        return {"success": True}

    @get("/list")
    @require(Session, judge=lambda x: x.get("login"))
    def list(self):
         file_dir = os.path.join(project_path, "static/secret")
         html_tmpl = "<html><header><title>我的私货</title></header><body><ul>%s</ul></body></html>"

         urls = list()
         for file in glob.glob(os.path.join(file_dir, "*")):
            urls.append(file.replace(project_path, ""))
         html = html_tmpl % "\n".join(f"<li><a href='{url}'>"
                                      f"{os.path.basename(url)}</a></li>" for url in urls)
         return html

