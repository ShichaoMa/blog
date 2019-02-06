import blog
import pytest

from pytest_apistellar import prop_alias
from blog.blog.article.article import Article
from blog.blog.article.article_exporter import ArticleExporter

project_path = blog.__path__[0]
article = prop_alias("blog.blog.article.article.Article")


@pytest.mark.asyncio
@pytest.mark.env(PROJECT_PATH=project_path)
class TestArticleExporter(object):
    async def test__choice_function(self):
        article = Article(id="me")
        article_exporter = ArticleExporter(article, "", "")
        assert article_exporter._choice_function() == article_exporter.export_me
        article = Article(id="xxx")
        article_exporter = ArticleExporter(article, "", "")
        assert article_exporter._choice_function() == article_exporter.export_other

    @article("right_code", ret_val=False)
    async def test_export_me_code_not_right(self):
        article = Article(id="me")
        article_exporter = ArticleExporter(article, "", "")
        with pytest.raises(AssertionError):
            await article_exporter.export_me()

    @article("right_code", ret_val=True)
    async def test_export_me_code_right(self):
        article = Article(id="me", tags=["a", "b"],
                          title="b", description="11", author="ma")
        article.format()
        article_exporter = ArticleExporter(article, "", "")
        article_file = await article_exporter.export_me()
        assert article_file.filename == "b.pdf"
        assert len(article_file.buffer) > 10

    @article("right_code", ret_val=True)
    async def test__replace_url(self):
        article_exporter = ArticleExporter("", "", "http://www.baidu.com/abc")
        html = '<img src="http://img.shields.io/aaa">' \
               '<img src="http://www.amazon.com/01.jpg">'
        html = article_exporter._replace_url(html)
        assert html.count("http://www.baidu.com/cut"
                          "?width=60&height=20&url=http://img.shields.io/aaa")
        assert html.count("http://www.amazon.com/01.jpg")

    @article("right_code", ret_val=False)
    async def test_export_other(self):
        article = Article(id="1234", tags=["a", "b"], article="1111",
                          title="b", description="11", author="ma")
        article_exporter = ArticleExporter(article, "", "")
        article_file = await article_exporter.export_other()
        assert article_file.filename == "b.md"
        assert article_file.buffer.count(b"comment") == 4