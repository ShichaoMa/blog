import os
import re
import hashlib
import asyncio
import zipfile
import markdown
import html2text

from io import BytesIO
from toolkit import cache_method
from concurrent.futures import ThreadPoolExecutor
from apistellar import FileResponse, Service, settings

from ..utils import get_id
from .article import Article
from .article_exporter import ArticleExporter


class ArticleService(Service):
    def __init__(self):
        self.phantomjs_path = settings.get("PHANTOMJS_PATH")
        self.js_path = os.path.join(settings["PROJECT_PATH"], "cut_html.js")
        self.executor = ThreadPoolExecutor()

    async def get(self, id):
        """
        获取文章对象，并渲染文章正文
        :param id:
        :return:
        """
        article = await Article.load(id=id)
        format_article_body = markdown.markdown(
            article.article,
            extensions=['markdown.extensions.extra'])
        article = article.to_dict()
        article["first_img"] = self._get_image(article.pop("article"))
        article["article"] = format_article_body
        return article

    async def export(self, article_list, code, url):
        """
        导出文章或文章列表，生成压缩包
        :param article_list:
        :param code:
        :param url:
        :return:
        """
        zip_file = BytesIO()
        zf = zipfile.ZipFile(zip_file, "w")
        for article in article_list:
            zf.writestr(*await ArticleExporter(article, code, url).export())

        zf.close()
        zip_file.seek(0)
        body = zip_file.read()
        zip_file.close()
        return FileResponse(body, filename=f"{get_id()}.zip")

    async def modify(self, article, img_url):
        """
        修改文章
        :param article:
        :param img_url:
        :return:
        """
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = False
        article.article = "[comment]: <image> (![](%s))\n%s" % (
            img_url, h2t.handle(article.article)
        )
        await article.update()

    async def update(self, article):
        """
        更新文章
        :param article:
        :return:
        """
        await article.update()

    async def delete(self, article):
        """
        删除文章
        :param article:
        :return:
        """
        await article.remove()

    async def about(self, id):
        """
        返回或者生成关于我和我的联系方式文章模板
        :param id:
        :return:
        """
        article = await Article.load(id=id)
        if not article:
            article.id = id
            article.author = self.settings.get("AUTHOR")
            article.tags = [id]
            article.description = id
            article.feature = False
            article.article = id
            article.title = id
            article.show = False
            article.format()
            await article.save()

        article = article.to_dict()
        article["first_img"] = self._get_image(article["article"])
        article["article"] = markdown.markdown(
            article["article"], extensions=['markdown.extensions.extra'])
        return article

    async def show(self, searchField, _from, size, fulltext):
        """
        首页展示
        :param searchField:
        :param _from:
        :param size:
        :param fulltext:
        :return:
        """
        # 获取精品文档
        feature_articles = await Article.search(
            searchField, _from=_from, size=size,
            fulltext=fulltext, feature=True, show=True)
        self._enrich_first_img(feature_articles)

        # 获取首页文档
        articles = await Article.search(
            searchField, _from=_from, size=size, fulltext=fulltext, show=True)
        self._enrich_first_img(articles)
        # 获取全部tags
        count, tags = await Article.get_total_tags()

        return {
            "count": count,
            "articles": articles,
            "feature_articles": feature_articles,
            "tags": list(sorted(tags.items(), key=lambda x: x[1], reverse=True))
        }

    async def cut(self, url, top, left, width, height):
        """
        按指定位置尺寸切网页
        :param url:
        :param top:
        :param left:
        :param width:
        :param height:
        :return:
        """

        sh = hashlib.sha1(url.encode())
        sh.update(bytes(str(top), encoding="utf-8"))
        sh.update(bytes(str(left), encoding="utf-8"))
        sh.update(bytes(str(width), encoding="utf-8"))
        sh.update(bytes(str(height), encoding="utf-8"))
        save_name = sh.hexdigest()[:10] + ".png"
        save_name = os.path.join(
            settings["PROJECT_PATH"], "static/temp/", save_name)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._cut,
            url, save_name, top, left, width, height)
        return save_name

    @classmethod
    def _enrich_first_img(cls, articles):
        for index in range(len(articles)):
            article = articles[index].to_dict()
            article["first_img"] = cls._get_image(article.pop("article"))
            articles[index] = article

    @staticmethod
    def _get_image(body):
        try:
            image_part = body[:body.index("\n")]
        except ValueError:
            image_part = body
        mth = re.search(r"!\[.*?\]\((.*?)\)", image_part)
        return mth.group(1) if mth else ""

    @cache_method(3600)
    def _cut(self, url, save_name, top=0, left=0, width=1024, height=768):
        os.system(("%s " * 8) % (
            self.phantomjs_path, self.js_path, url,
            save_name, top, left, width, height))
