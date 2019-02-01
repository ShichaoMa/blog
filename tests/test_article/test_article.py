import os
import pytest

from pytest_apistellar import prop_alias
from pytest_apistellar.parser import Attr

from blog.blog.article.article import Article
from blog.blog.utils import project_path


article = prop_alias("blog.blog.article.article.Article")


def get_code():
    code, _ = open(os.path.join(project_path, "code")).read().split("\n")
    return code


def assert_execute(sql, args, assert_sql, assert_args, **kwargs):
    assert sql == assert_sql
    assert args == assert_args


@article("code", ret_val=get_code())
@pytest.mark.env(NEED_CODE="False")
@pytest.mark.env(CODE_EXPIRE_INTERVAL=30 * 24 * 3600)
@pytest.mark.asyncio
class TestArticle(object):

    pytestmark = [
        article("store", ret_val=Attr()),
        article("store.execute", callable=True)
    ]

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_True(self):
        assert Article().right_code(get_code()) is True

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_False(self):
        assert Article().right_code("111111") is False

    async def test_check_code_off(self):
        assert Article().right_code("111111") is True

    @article("store.description", ret_val=[("id", )])
    @article("store.fetchone", ret_val=("111", ), callable=True)
    async def test_load_with_article(self):
        article = await Article.load()
        assert article["id"] == "111"

    @article("store.execute", ret_factory=assert_execute,
             assert_sql=f"INSERT INTO {Article.TABLE} "
                        f"VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
             assert_args=("2017010101010", "ccc", "aaa,bbb", "dddd", "夏洛之枫",
                          "aaa", True, 1539140711.0, 1539140711.0, False))
    async def test_save(self):
        data = {
            "id": "2017010101010",
            "description": "ccc",
            "tags": "aaa,bbb",
            "article": "dddd",
            "author": "夏洛之枫",
            "title": "aaa",
            "feature": "1",
            "created_at": "2018-10-10 11:11:11",
            "updated_at": "2018-10-10 11:11:11",
            "show": "0"
        }
        article = Article(data)
        await article.save()

    @article("store.execute", ret_factory=assert_execute,
             assert_sql=f"DELETE FROM {Article.TABLE} WHERE show=1 and id=?;",
             assert_args=("2017010101010", ))
    async def test_remove(self):
        article = Article(id="2017010101010")
        await article.remove()

    @article("_build_update_sql", ret_val=("test_sql", ["1"]))
    @article("store.execute", ret_factory=assert_execute,
             assert_sql="test_sql",
             assert_args=["1"])
    async def test_update(self):
        data = {
            "id": "2017010101010",
            "description": "ccc",
            "show": "0"
        }
        article = Article(data)
        await article.update()

    @article("store.fetchone", callable=True)
    async def test_load_without_article(self):
        assert "id" not in await Article.load()

    async def test_fuzzy_search_sub_sql_without_field(self):
        assert Article._fuzzy_search_sub_sql("", False) == (None, None)

    async def test_fuzzy_search_sub_sql_with_field_fulltext(self):
        sub, vals = Article._fuzzy_search_sub_sql("abc", True)
        assert sub == "AND (article LIKE ? OR tags LIKE ?)"
        assert vals == ['%abc%', '%abc%']

    async def test_fuzzy_search_sub_sql_with_field_fulltext_false(self):
        sub, vals = Article._fuzzy_search_sub_sql("abc", False)
        assert sub == "AND tags LIKE ?"
        assert vals == ['%abc%']

    async def test_build_select_sql_with_no_args(self):
        vals, sql = Article._build_select_sql()
        assert vals == list()
        assert sql == f"SELECT * FROM {Article.TABLE} WHERE 1=1;"

    async def test_build_select_sql_with_vals_and_sub(self):
        vals, sql = Article._build_select_sql(vals=["name"], sub=" AND title=?")
        assert vals == ["name"]
        assert sql == f"SELECT * FROM {Article.TABLE} WHERE 1=1 AND title=?;"

    async def test_build_select_sql_with_kwargs_of_in_opt(self):
        vals, sql = Article._build_select_sql({"id": ["1", "2"], "title": "a"})
        assert "1" in vals
        assert "2" in vals
        assert "a" in vals
        assert "id IN (?, ?)" in sql
        assert "title=?" in sql

    async def test_build_select_sql_with_order_fields(self):
        vals, sql = Article._build_select_sql(
            order_fields=[("id", "desc"), ("title", "asc")])
        assert vals == []
        assert "id desc" in sql
        assert "title asc" in sql

    async def test_build_select_sql_with_size_and_from(self):
        vals, sql = Article._build_select_sql(size=10, _from=0)
        assert vals == []
        assert "limit 10 offset 0" in sql

    async def test_build_select_sql_with_size_and_without_from(self):
        with pytest.raises(AssertionError):
            Article._build_select_sql(size=10)

    async def test_build_update_sql(self):
        data = {
            "id": "2017010101010",
            "tags": "aaa,bbb",
            "feature": "1"
        }
        article = Article(data)
        sql, args = Article._build_update_sql(article)
        assert sql == f"UPDATE {Article.TABLE} SET tags=?, feature=?, " \
                      f"updated_at=? WHERE id=?;"
        assert args[0] == "aaa,bbb"
        assert args[1] is True
        assert args[3] == "2017010101010"
