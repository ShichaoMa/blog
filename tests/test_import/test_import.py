import pytest

from apistellar import settings
from pytest_apistellar import prop_alias

from blog.blog.import_ import Import, Article

article = prop_alias("blog.blog.article.article.Article")


@pytest.mark.asyncio
class TestImport(object):

    async def test_retrieve_success(self):
        article = ["aaaa", "[comment]: <title> (abcde)"]
        val = Import.retrieve("title", article)
        assert val == "abcde"
        assert len(article) == 1
        assert article[0] == "aaaa"

    async def test_retrieve_failed(self):
        article = ["aaaa"]
        val = Import.retrieve("title", article)
        assert val == ""

    @article("load", ret_val=Article())
    @article("save")
    async def test_insert(self, join_root_dir):
        article = await Import.insert(
            join_root_dir("test_data/一键生成API文档.md"))
        assert article.title == "一键生成API文档"
        assert article.tags == []
        assert article.author == settings["AUTHOR"]

    @article("load", ret_val=Article(title="已存在的文件", tags=["1"]))
    @article("save")
    async def test_insert_exists(self, join_root_dir):
        article = await Import.insert(
            join_root_dir("test_data/一键生成API文档.md"))
        assert article.title == "已存在的文件"
        assert article.tags == ["1"]
