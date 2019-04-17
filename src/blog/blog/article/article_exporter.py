import os
import re
import asyncio
import markdown

from functools import partial
from urllib.parse import urljoin
from collections import namedtuple
from apistellar import settings


ArticleFile = namedtuple("ArticleFile", "filename,buffer")


class ArticleExporter(object):
    __slots__ = ("article", "code", "url")
    desc_fields = ("tags", "description", "title", "author")

    def __init__(self, article, code, url):
        self.article = article
        self.code = code
        self.url = url

    async def export_pdf(self, content):
        from html.parser import unescape
        html = unescape(markdown.markdown(
            content, extensions=['markdown.extensions.extra']))
        return await self._get_pdf_buffer(
            f'<div class="markdown-body">{self._replace_url(html)}</div>')

    async def export_me(self):
        """
        导出我的简历
        :return:
        """
        assert self.article.right_code(self.code), f"Invalid code: {self.code}"
        buffer = await self.export_pdf(self.article.article)
        return ArticleFile(f"{self.article.title}.pdf", buffer)

    @classmethod
    async def save_as_pdf(cls, content, path):
        """
        将网页转换pdf
        :param html:
        :return:
        """
        with open(path, "wb") as f:
            f.write(await cls._get_pdf_buffer(content))

    @staticmethod
    async def _get_pdf_buffer(html):
        from weasyprint import HTML

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(HTML(string=html).write_pdf, stylesheets=[
                os.path.join(settings["PROJECT_PATH"], "static/css/pdf.css")]))

    async def export_other(self):
        """
        导出其它文章
        :return:
        """
        buffer = self.article.article
        for field in self.desc_fields:
            buffer += "\n"
            buffer += f"[comment]: <{field}> ({getattr(self.article, field)})"

        return ArticleFile(f"{self.article.title}.md", buffer.encode())

    async def export(self):
        return await (self._choice_function()())

    def _choice_function(self):
        return getattr(self, f"export_{self.article.id}", self.export_other)

    def _replace_url(self, html):
        return re.sub(r'(?<=src=")(.+?)(?=")', self._repl, html)

    def _repl(self, mth):
        """
        由于weasyprint有bug会让svg失真，所以将svg的图片截一下。
        :param mth:
        :return:
        """
        url = mth.group(1)
        if not url.count("img.shields.io"):
            return url

        return urljoin(self.url, "/cut") + f"?width=60&height=20&url={url}"
