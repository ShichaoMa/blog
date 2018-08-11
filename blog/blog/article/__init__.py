import typing

from apistar import http, App
from toolkit.settings import FrozenSettings
from star_builder.helper import redirect
from star_builder import Controller, route, get, post, Session, require

from .article import Article
from ..utils import project_path
from ..components import FormParam
from .service import ArticleService


@route("", name="article")
class ArticleController(Controller):

    @get("/import")
    @require(Session)
    async def _import(app: App,
                article: Article,
                session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        else:
            return app.render_template("import.html", success="", **article.to_dict())

    @post("/check")
    async def check(app: App,
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
                f"{ref}.html", success="", ref=ref, **article.to_dict())
        else:
            return app.render_template("login.html", ref=ref, **article.to_dict())

    @get('/load')
    async def load(username: FormParam,
             password: FormParam,
             settings: FrozenSettings,
             session: Session):
        if username == settings.USERNAME and password == settings.PASSWORD:
            session["login"] = f'{username}:{password}'
            return {"result": 1}
        else:
            return {"result": 0}

    @post("/upload")
    async def upload(app: App,
               article: Article,
               session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        await article.save()
        return app.render_template("import.html", success="success")

    @get("/export")
    async def export(url: http.URL,
                code: http.QueryParam,
                service: ArticleService,
                article_list: typing.List[Article]):
        return await service.export(article_list, code, url)

    @post("/modify")
    async def modify(img_url: FormParam,
               service: ArticleService,
               article: Article,
               session: Session):
        if not session.get("login"):
            return {"result": 0}
        await service.modify(article, img_url)
        return {"result": 1}

    @get("/edit")
    async def edit(app: App,
             article: Article,
             session: Session):
        await article.load()
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        else:
            return app.render_template("edit.html", ref="update", **article)

    @post("/update")
    async def update(app: App,
             article: Article,
             service: ArticleService,
             session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        await service.update(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/delete")
    async def delete(app: App,
             article: Article,
             service: ArticleService,
             session: Session):
        if not session.get("login"):
            return app.render_template(
                "login.html", ref="delete", id=article.id)
        await service.delete(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/article", name="article")
    async def get_article(article: Article,
             service: ArticleService):
        return await service.get(article)

    @get("/me")
    async def me(article: Article,
                 code: http.QueryParam,
                 service: ArticleService):
        if not service.check_code(code):
            return {"error": True}
        return await service.about(article, "me")

    @get("/contact")
    async def contact(article: Article,
                 service: ArticleService):
        return await service.about(article, "contact")

    @get("/show")
    async def show(searchField: http.QueryParam,
             fulltext: http.QueryParam,
             service: ArticleService,
             _from: http.QueryParam,
             size: http.QueryParam):
       return await service.show(searchField, _from, size, fulltext)

    @get("/cut")
    async def cut(service: ArticleService,
            url: http.QueryParam,
            top: int=0,
            left: int=0,
            width: int=1024,
            height: int=768):
        save_name = await service.cut(url, top, left, width, height)
        return redirect(save_name.replace(project_path, ""))
