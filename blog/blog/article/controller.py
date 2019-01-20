from apistar import http, App
from apistellar.helper import redirect, return_wrapped
from apistellar import Controller, route, get, post, \
    Session, FormParam, SettingsMixin, require, UrlEncodeForm, MultiPartForm

from .article import Article
from blog.utils import project_path, decode
from .service import ArticleService


@route("", name="article")
class ArticleController(Controller, SettingsMixin):
    """
    文章相关的api
    """
    def __init__(self):
        # 通过在controller中初始化service会失去service的注入功能，
        # service全局唯一，无法随请求的改变而改变。
        # 但好处是不用每次请求重新创建service对象了。
        # 对于不需要注入属性能service可以使用此方案。
        self.service = ArticleService()

    @get("/import")
    async def _import(self, app: App, session: Session):
        """
        导入文章
        :param app:
        :param session:
        :return: 导入文章页面
        """
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        else:
            return app.render_template("import.html", success="")

    @post("/check")
    async def check(self,
                    app: App,
                    article: Article,
                    username: FormParam,
                    password: FormParam,
                    ref: FormParam,
                    session: Session):
        """
        检查用户名和密码是否正确
        :param app:
        :param article:
        :ex article:
        ```json
        {"title": "xxx"}
        ```
        :type article: form
        :param username: 用户名
        :ex username: `test`
        :param password: 密码
        :ex password: `12345`
        :param ref: 从哪里跳过来的
        :param session:
        :return: 返回网页
        """
        # article由于没有经过format会带有多余的信息
        if username == self.settings["USERNAME"] and \
                password == self.settings["PASSWORD"]:
            session["login"] = f'{username}:{password}'
            if ref == "edit" and hasattr(article, "id"):
                article = await article.load()
            if ref:
                return app.render_template(
                    f"{ref}.html", success="", **article.to_dict())
            else:
                return redirect(app.reverse_url("view:welcome:index"))
        else:
            return app.render_template(
                "login.html", **article.to_dict())

    @get('/load')
    @return_wrapped(error_info={401: "密码错误"})
    async def load(self,
                   username: http.QueryParam,
                   password: http.QueryParam,
                   session: Session):
        """
        检查用户名密码是否正确，返回检查结果
        :param username: 用户名
        :ex username: `test`
        :param password: 密码
        :ex password: `12345`
        :param session:
        :return:
        ```json
        {"code": 0, "data": null}
        ```
        :return:
        ```json
        {"code": 401, "message": "密码错误"}
        ```
        """
        assert username == self.settings["USERNAME"] and \
                password == self.settings["PASSWORD"], (401, "密码错误")
        session["login"] = f'{username}:{password}'

    @post("/upload")
    async def upload(self, app: App, article: Article, session: Session):
        """
        用于上传文章
        :param app:
        :param article: 文章相关信息
        :param session:
        :return: 返回上传页面继续上传
        """
        if not session.get("login"):
            return app.render_template("login.html", ref="import")
        article["title"] = article.title or \
                           article.article.filename.replace(".md", "")
        article["article"] = decode(article.article.read())
        await article.save()
        return app.render_template("import.html", success="success")

    @get("/export")
    async def export(self,
                     url: http.URL,
                     code: http.QueryParam,
                     ids: http.QueryParam):
        """
        导出文章
        :param url: 当前访问的url地址
        :param code: 后端生成的用于验证的code
        :param ids: 要导出的文章id，使用,连接成字符串
        :ex ids: `20181010111111,20181020111111`
        :return: 导出生成的压缩包
        """
        if ids:
            ids = ids.split(",")
        else:
            ids = []
        article_list = await Article.load_list(ids)
        return await self.service.export(article_list, code, url)

    @post("/modify")
    @return_wrapped(error_info={401: "Login required!"})
    @require(Session, judge=lambda x: x.get("login"))
    async def modify(self, img_url: FormParam, article: Article):
        """
        这个接口用于直接在网页上修改文章内容
        :param img_url: 首图地址
        :ex img_url: `http://www.csdn.....jpg`
        :param article: 文章对象
        :type article: form
        :param session:
        :return:
        ```json
        {"code": 0, "data": null}
        ```
        :return:
        ```json
        {"code": 401, "message": "Login required!"}
        ```
        """
        return await self.service.modify(article, img_url)

    @get("/edit")
    async def edit(self, app: App, id: http.QueryParam, session: Session):
        """
        打开文章编辑页面
        :param app:
        :param id: 文章的id
        :ex id: `20111111111111`
        :param session:
        :return: 如果登录了，跳转到编辑页面，否则，跳转到登录页。
        """
        article = Article(id=id)
        await article.load()

        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)
        else:
            return app.render_template("edit.html", ref="update", **article)

    @post("/update")
    async def update(self, app: App, article: Article, session: Session):
        """
        编辑之后更新文章内容
        :param app:
        :param article: 文章对象
        :type article: form
        :param session:
        :return: 如果登录了，跳转到首页，否则，跳转到登录页
        """
        if not session.get("login"):
            return app.render_template("login.html", ref="edit", **article)

        await self.service.update(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/delete")
    async def delete(self, app: App, id: http.QueryParam, session: Session):
        """
        删除文章接口
        :param app:
        :param id: 要删除的文章id
        :ex id: `19911111111111`
        :param session:
        :return: 如果登录了，跳转到首页，否则跳转到登录页。
        """
        article = Article(id=id)
        if not session.get("login"):
            return app.render_template(
                "login.html", ref="delete", id=article.id)

        await self.service.delete(article)
        return redirect(app.reverse_url("view:welcome:index"))

    @get("/article", name="article")
    async def get_article(self, id: http.QueryParam) -> Article:
        """
        获取文章
        :param id: 要获取的文章id
        :return: 获取到的文章对象
        """
        return await self.service.get(id)

    @get("/me")
    async def me(self, code: http.QueryParam) -> Article:
        """
        获取关于我的文章
        :param code: 后端生成的用于验证的code
        :return: 获取到的文章对象
        """
        assert Article.right_code(code), f"Invalid code: {code}"
        return await self.service.about("me")

    @get("/contact")
    async def contact(self) -> Article:
        """
        获取我的联系方式
        :param code: 后端生成的用于验证的code
        :return: 获取到的文章对象
        """
        return await self.service.about("contact")

    @get("/show")
    async def show(self,
                   searchField: http.QueryParam="",
                   fulltext: bool=True,
                   _from: int=0,
                   size: int=10):
        """
        首页展示接口
        :param searchField: 搜索关键词
        :ex searchField: `python`
        :param fulltext: 是否全文搜索
        :ex fulltext: `true/false`
        :param _from: 从第几篇文章开始搜
        :ex _from: `0`
        :param size: 每页大小
        :ex size: `10`
        :return:
        ```json
        {
            "count": 10,
            "articles": [...],
            "feature_articles": [..],
            "tags": ["python", "ubuntu"...]
        }
        ```
        """
        return await self.service.show(searchField, _from, size, fulltext)

    @get("/cut")
    async def cut(self,
                  url: http.QueryParam,
                  top: int=0,
                  left: int=0,
                  width: int=1024,
                  height: int= 768):
        """
        截图api
        :param url: 要截图的地址
        :param top: 截图区域的top
        :param left: 截图区域的left
        :param width: 截图区域的width
        :param height: 截图区域的height
        :return: 重定向到截图的静态地址
        """
        save_name = await self.service.cut(url, top, left, width, height)
        return redirect(save_name.replace(project_path, ""))
