import re
import os
import asyncio
import zipfile
import markdown
import html2text

from io import BytesIO
from apistar import http
from functools import partial
from urllib.parse import urljoin, urlparse
from toolkit.settings import FrozenSettings
from star_builder import FileResponse, Repository
from concurrent.futures import ProcessPoolExecutor

from ..lib import Sqlite
from .article import Article
from ..components import Code
from ..lib.html_cut import Cuter
from ..utils import get_cut_file_name, project_path, \
    get_id, format_articles, get_image


class ArticleRepository(Repository):

    def __init__(self):
        self.executor = ProcessPoolExecutor()

    def resolve(self,
                cuter: Cuter,
                code: Code,
                url: http.URL,
                sqlite: Sqlite,
                settings: FrozenSettings):
        self.cuter = cuter
        self.code = code
        self.url = url
        self.sqlite = sqlite
        self.settings = settings
        return self

    def _repl(self, mth):
        url = mth.group(1)
        if not url.startswith("/cut"):
            return url
        parts = urlparse(url)
        params = dict(p.split("=", 1) for p in parts.query.split("&"))
        return urljoin(self.url, get_cut_file_name("", **params).strip("/"))

    def check_code(self, code):
        return code == self.code

    async def get(self, article):
        await article.load()
        format_article_body = markdown.markdown(
            article.article,
            extensions=['markdown.extensions.extra'])
        _, articles = format_articles([article.to_dict()])
        article = articles.pop()
        article["article"] = format_article_body
        return article

    async def export(self, article_list, code):
        zip_file = BytesIO()
        zf = zipfile.ZipFile(zip_file, "w")
        for article in article_list:
            ext = "md"
            if article.id == "me":
                if not self.check_code(code):
                    return {"error": True}
                from html.parser import unescape
                from weasyprint import HTML
                from urllib.parse import urlparse, urljoin
                html = markdown.markdown(
                    article.article, extensions=['markdown.extensions.extra'])
                html = unescape(html)

                html = '<div class="markdown-body">%s</div>' % re.sub(
                    r'(?<=src\=")(.+?)(?=")', self._repl, html)
                loop = asyncio.get_event_loop()
                buffer = await loop.run_in_executor(
                    None, partial(HTML(string=html).write_pdf, stylesheets=[
                        os.path.join(project_path, "static/css/pdf.css")]))
                ext = "pdf"
            else:
                buffer = "\n".join(
                    [article.article,
                     "[comment]: <tags> (%s)" % article.tags,
                     "[comment]: <description> (%s)" % article.description,
                     "[comment]: <title> (%s)" % article.title,
                     "[comment]: <author> (%s)" % article.author,
                ]).encode()
            zf.writestr("%s.%s" % (article.title, ext),  buffer)
        zf.close()
        zip_file.seek(0)
        body = zip_file.read()
        zip_file.close()
        return FileResponse(body, filename=f"{get_id()}.zip")

    async def modify(self, article, img_url):
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = False
        article.article = "[comment]: <image> (![](%s))\n%s" % (
            img_url, h2t.handle(article.article)
        ),
        await article.update()

    async def update(self, article):
        await article.update()

    async def delete(self, article):
        await article.remove()

    async def about(self, article, id):
        await article.load(id=id)
        if not article:
            article.id = id
            article.author = self.settings.AUTHOR
            article.tags = [id]
            article.description = id
            article.feature = False
            article.article = id
            article.title = id
            article.show = False
            article.format()
            await article.save()

        article = article.to_dict()
        article["first_img"] = get_image(article["article"])
        article["article"] = markdown.markdown(
            article["article"], extensions=['markdown.extensions.extra'])
        return article

    async def show(self, searchField, _from, size, fulltext):
        Article.init(sqlite=self.sqlite)
        articles = await Article.search(
            searchField, _from=_from, size=size,
            fulltext=fulltext == "true", show=True)

        feature_articles = await Article.search(
            searchField, _from=_from, size=size,
            fulltext=fulltext == "true", feature=True, show=True)
        tags = [article.tags for article in
                await Article.load_list(None, projection=["tags"], show=True)]
        count = len(tags)
        tags, articles = format_articles(
            [article.to_dict() for article in articles], tags=tags)
        _, feature_articles = format_articles(
            [article.to_dict() for article in feature_articles])
        return {
            "count": count,
            "articles": articles,
            "feature_articles": feature_articles,
            "tags": [i for i in
                     sorted(tags.items(), key=lambda x: x[1], reverse=True)]}

    async def cut(self, url, top, left, width, height):
        save_name = get_cut_file_name(
            project_path, url, top, left, width, height)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.cuter.cut,
            url, save_name, top, left, width, height)
        return save_name
