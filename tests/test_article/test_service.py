import blog
import pytest

from io import BytesIO
from zipfile import ZipFile
from collections import defaultdict
from pytest_apistellar import prop_alias
from toolkit.settings import SettingsLoader

from blog.blog.article.service import ArticleService, Article
from blog.blog.article.article_exporter import ArticleFile
arti_ser = prop_alias("blog.blog.article.service.ArticleService")
article = prop_alias("blog.blog.article.article.Article")

project_path = blog.__path__[0]


@arti_ser("settings", ret_val=SettingsLoader().load("blog.settings"))
@pytest.mark.env(PROJECT_PATH=project_path)
@pytest.mark.asyncio
class TestService(object):

    @article("load", ret_val=Article(id="20181010101010",
                                     article="![](http://www.baidu.com/)"))
    async def test_get(self):
        article = await ArticleService().get("20181010101010")
        assert article["first_img"] == "http://www.baidu.com/"

    @pytest.mark.prop(
        "blog.blog.article.article_exporter.ArticleExporter.export",
        ret_val=ArticleFile("test.pdf", b"aaaaa"))
    async def test_export(self):
        file_resp = await ArticleService().export([1], "", "")
        zip_file = BytesIO(file_resp.content)
        zf = ZipFile(zip_file)
        for file in zf.infolist():
            assert file.filename == "test.pdf"
            assert file.file_size == 5

    @article("update")
    async def test_modify(self):
        article = Article(article="<h1>aaa</h1>")
        await ArticleService().modify(article, "http://www.baidu.com/")
        assert article.article == "[comment]: <image> (![]" \
                                  "(http://www.baidu.com/))\n# aaa\n\n"

    @article("update")
    async def test_update(self):
        article = Article(id="20180101010101")
        await ArticleService().update(article)
        assert article.to_dict() == {"id": "20180101010101"}

    @article("remove")
    async def test_remove(self):
        article = Article(id="20180101010101")
        await ArticleService().delete(article)
        assert article.to_dict() == {"id": "20180101010101"}

    @article("load", ret_val=Article(id="me",
                                     article="![](http://www.baidu.com/)"))
    async def test_about_with_article(self):
        article = await ArticleService().about("me")
        assert article["first_img"] == "http://www.baidu.com/"
        assert article["article"] == '<p><img alt="" src="http://www.baidu.com/" /></p>'

    @article("load", ret_val=Article())
    @article("save")
    @pytest.mark.env(AUTHOR="test")
    async def test_about_without_article(self):
        id = "me"
        article = await ArticleService().about(id)
        assert article["first_img"] == ""
        assert article["author"] == "test"
        assert article["tags"] == id
        assert article["description"] == id
        assert article["feature"] is False
        assert article["title"] == id
        assert article["show"] is False
        assert article["article"] == "<p>" + id + "</p>"
        assert "updated_at" in article
        assert "created_at" in article

    @article("search", ret_factory=
    lambda *args, **kwargs: [Article(article="![](http://www.baidu.com/)")])
    @article("get_total_tags", ret_val=(1, defaultdict(a=1, b=2)))
    async def test_show(self):
        rs = await ArticleService().show("", 0, 10, False)
        article = dict()
        article["first_img"] = "http://www.baidu.com/"
        assert rs["count"] == 1
        assert rs["tags"] == [("b", 2), ("a", 1)]
        assert rs["feature_articles"][0] == article
        assert rs["articles"][0] == article

    @pytest.mark.prop("asyncio.unix_events._UnixSelectorEventLoop.run_in_executor", asyncable=True)
    async def test_cut(self):
        save_name = await ArticleService().cut(
            "http://www.baidu.com/", 0, 0, 1024, 768)
        assert save_name == "1169ee22f8.png"
