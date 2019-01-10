import typing

from apistar import http, App
from toolkit.settings import FrozenSettings
from apistellar.helper import redirect
from apistellar import Controller, route, get, post, Session, FormParam
#from apistellar.bases.entities import comment

from .article import Article
from ..utils import project_path
from .service import ArticleService

def comment(type, _):
    return type

@route("", name="article")
class ArticleController(Controller):

    def __init__(self):
        # 通过在controller中初始化service会失去service的注入功能，
        # service全局唯一，无法随请求的改变而改变。
        # 但好处是不用每次请求重新创建service对象了。
        # 对于不需要注入属性能service可以使用此方案。
        self.service = ArticleService()

    @get("/import")
    async def _import(self, app: App, article: Article, session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        else:
            return app.render_template("import.html", success="",
                                       **article.to_dict())

    @post("/check")
    async def check(self,
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
                f"{ref}.html", success="", ref=ref, **article.to_dict())
        else:
            return app.render_template("login.html", ref=ref,
                                       **article.to_dict())

    @get('/load')
    async def load(self,
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
    async def upload(self, app: App, article: Article, session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        await article.save()
        return app.render_template("import.html", success="success")

    @get("/export")
    async def export(self,
                     url: http.URL,
                     code: http.QueryParam,
                     article_list: typing.List[Article]):
        return await self.service.export(article_list, code, url)

    @post("/modify")
    async def modify(self, img_url: FormParam, article: Article, session: Session):
        if not session.get("login"):
            return {"result": 0}
        await self.service.modify(article, img_url)
        return {"result": 1}

    @get("/edit")
    async def edit(self, app: App, article: Article, session: Session):
        await article.load()
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        else:
            return app.render_template("edit.html", ref="update", **article)

    @post("/update")
    async def update(self, app: App, article: Article, session: Session):
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        await self.service.update(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/delete")
    async def delete(self, app: App, article: Article, session: Session):
        if not session.get("login"):
            return app.render_template(
                "login.html", ref="delete", id=article.id)
        await self.service.delete(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/article", name="article")
    async def get_article(self, article: Article):
        return await self.service.get(article)

    @get("/me")
    async def me(self, article: Article, code: http.QueryParam):
        assert article.right_code(code), f"Invalid code: {code}"
        return await self.service.about(article, "me")

    @get("/contact")
    async def contact(self):
        return await self.service.about(article, "contact")

    @get("/show")
    async def show(self,
                   searchField: http.QueryParam,
                   fulltext: http.QueryParam,
                   _from: http.QueryParam,
                   size: http.QueryParam):
        return await self.service.show(searchField, _from, size, fulltext)

    @get("/cut")
    async def cut(self,
                  url: comment(http.QueryParam, "要截图的url连接"),
                  top: comment(int, "截图尺寸top值") = 0,
                  left: comment(int, "截图尺寸left值") = 0,
                  width: comment(int, "截图尺寸width值") = 1024,
                  height: comment(int, "截图尺寸height值") = 768) -> comment(Article, "返回"):
        """
        截图api
        """
        save_name = await self.service.cut(url, top, left, width, height)
        return redirect(save_name.replace(project_path, ""))
