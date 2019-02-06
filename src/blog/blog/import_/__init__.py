import re
import glob
import time
from logging import getLogger

from os.path import join, basename
from apistellar import Solo, settings

from ..article.article import Article


logger = getLogger("import")


class Import(Solo):

    def __init__(self, paths, **kwargs):
        self.paths = paths
        super(Import, self).__init__(**kwargs)

    async def setup(self):
        """
        初始化
        :return:
        """

    async def run(self):
        """
        业务逻辑
        :return:
        """
        for path in self.paths:
            for filename in glob.glob(join(path, "*")):
                await self.insert(filename)

    @classmethod
    async def insert(cls, filename):
        title = basename(filename).replace(".md", "")
        article = await Article.load(title=title)

        if not article:
            article.title = title
            lines = open(filename, encoding="utf-8").readlines()
            article.tags = cls.retrieve("tags", lines) or []
            article.description = cls.retrieve("description", lines)
            article.title = cls.retrieve("title", lines) or title
            article.author = cls.retrieve("author", lines) or settings["AUTHOR"]
            article.article = "".join(lines)
            article.format()
            await article.save()
            time.sleep(1)
            logger.debug(f"Import {filename} to db. ")
        else:
            logger.info(f"Article {filename} exist. ")
        return article

    @staticmethod
    def retrieve(word, article):
        regex = re.compile(r"\[comment\]: <%s> \((.+?)\)" % word)
        for line in article[:]:
            mth = regex.search(line)
            if mth:
                article.remove(line)
                return mth.group(1)
        return ""

    async def teardown(self):
        """
        回收资源
        :return:
        """

    @classmethod
    def enrich_parser(cls, sub_parser):
        """
        自定义命令行参数，若定义了，则可通过__init__获取
        注意在__init__中使用kwargs来保留其它参数
        :param sub_parser:
        :return:
        """
        sub_parser.add_argument("paths", nargs="+", help="目录地址")

