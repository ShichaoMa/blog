import typing
import markdown

from apistar import http, App
from toolkit.settings import FrozenSettings
from star_builder.helper import redirect
from star_builder import Service, route, get, post, Session
from .article import Article
from ..components import Code, FormParam, Cuter, Sqlite
from ..utils import get_cut_file_name, now, format_articles, get_image, project_path
from .repository import ArticleRepository


@route("", name="article")
class ArticleService(Service):

    @get("/import")
    async def _import(self: Service,
                app: App,
                article: Article,
                session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        else:
            return app.render_template("import.html", success="", **article.to_json())

    @post("/check")
    async def check(self: Service,
                app: App,
                article: Article,
                username: FormParam,
                password: FormParam,
                ref: FormParam,
                settings: FrozenSettings,
                session: Session):
        if username == settings.USERNAME and password == settings.PASSWORD:
            session["login"] = f'{username}:{password}'
            if hasattr(article, "id"):
                article = await article.load()
            return app.render_template(
                f"{ref}.html", success="", ref=ref, **article.to_json())
        else:
            return app.render_template("login.html", ref=ref, **article.to_json())

    @get('/load')
    async def load(self: Service,
             username: FormParam,
             password: FormParam,
             settings: FrozenSettings,
             session: Session):
        if username == settings.USERNAME and password == settings.PASSWORD:
            session["login"] = f'{username}:{password}'
            return {"result": 1}
        else:
            return {"result": 0}

    @post("/upload")
    async def upload(self: Service,
               app: App,
               article: Article,
               session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        await article.save()
        return app.render_template("import.html", success="success")

    @get("/export")
    async def export(self: Service,
               code: http.QueryParam,
               repo: ArticleRepository,
               article_list: typing.List[Article],
               ):
        return await repo.export(article_list, code)

    @post("/modify")
    async def modify(self: Service,
               img_url: FormParam,
               repo: ArticleRepository,
               article: Article,
               session: Session):
        if not session.get("login"):
            return {"result": 0}
        await repo.modify(article, img_url)
        return {"result": 1}

    @get("/edit")
    async def edit(self: Service,
             app: App,
             article: Article,
             session: Session):
        await article.load()
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        else:
            return app.render_template("edit.html", ref="update", **article)

    @post("/update")
    async def update(self: Service,
             app: App,
             article: Article,
             repo: ArticleRepository,
             session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        await repo.update(article)
        return redirect(app.reverse_url("service:welcome:index"))

    @get("/delete")
    async def delete(self: Service,
             app: App,
             article: Article,
             repo: ArticleRepository,
             session: Session):
        if not session.get("login"):
            return app.render_template(
                "login.html", ref="delete", id=article.id)
        await repo.delete(article)
        return redirect(app.reverse_url("service:welcome:index"))

    @get("/article", name="article")
    async def get_article(self: Service,
             article: Article,
             repo: ArticleRepository):
        return await repo.get(article)

    @get("/me")
    async def me(self: Service,
                 article: Article,
                 code: http.QueryParam,
                 repo: ArticleRepository):
        if not repo.check_code(code):
            return {"error": True}
        return await repo.about(article, "me")

    @get("/contact")
    async def contact(self: Service,
                 article: Article,
                 repo: ArticleRepository):
        return await repo.about(article, "contact")

    @get("/show")
    async def show(self: Service,
             searchField: http.QueryParam,
             fulltext: http.QueryParam,
             repo: ArticleRepository,
             _from: http.QueryParam,
             size: http.QueryParam):
       return await repo.show(searchField, _from, size, fulltext)

    @get("/cut")
    async def cut(repo: ArticleRepository,
            url: http.QueryParam,
            top: http.QueryParam,
            left: http.QueryParam,
            width: http.QueryParam,
            height: http.QueryParam):
        top = top or 0
        left = left or 0
        width = width or 1024
        height = height or 768
        save_name = await repo.cut(url, top, left, width, height)
        return redirect(save_name.replace(project_path, ""))
