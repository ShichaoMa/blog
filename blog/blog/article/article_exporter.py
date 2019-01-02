import os
import re
import asyncio
import markdown

from functools import partial
from collections import namedtuple
from urllib.parse import urlunparse, urlparse

from ..utils import project_path


ArticleFile = namedtuple("ArticleFile", "filename,buffer")


class ArticleExporter(object):
    __slots__ = ("article", "code", "netloc", "scheme")
    desc_fields = ("tags", "description", "title", "author")

    def __init__(self, article, code, url):
        self.article = article
        self.code = code
        parts = urlparse(url)
        self.netloc = parts.netloc
        self.scheme = parts.scheme

    async def export_me(self):
        """
        导出我的简历
        :return:
        """
        assert self.article.right_code(self.code), f"Invalid code: {self.code}"

        from html.parser import unescape
        from weasyprint import HTML
        html = unescape(markdown.markdown(
            self.article.article, extensions=['markdown.extensions.extra']))
        html = f'<div class="markdown-body">{self._replace_url(html)}</div>'

        loop = asyncio.get_event_loop()
        buffer = await loop.run_in_executor(
            None, partial(HTML(string=html).write_pdf, stylesheets=[
                os.path.join(project_path, "static/css/pdf.css")]))
        return ArticleFile(f"{self.article.title}.pdf", buffer)

    def _replace_url(self, html):
        return re.sub(r'(?<=src=")(.+?)(?=")', self._repl, html)

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

    def _repl(self, mth):
        """
        将匹配到的内部地址替换成带协议和域名的绝对地址，不然pdf渲染工具无法访问。
        :param mth:
        :return:
        """
        url = mth.group(1)
        if url.startswith("http"):
            return url

        parts = urlparse(url)
        return urlunparse(parts._replace(scheme=self.scheme, netloc=self.netloc))
