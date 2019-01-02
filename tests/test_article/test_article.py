import os
import pytest

from collections import OrderedDict
from pytest_apistellar import prop_alias

from blog.blog.article.article import Article
from blog.blog.utils import project_path


article = prop_alias("blog.blog.article.article.Article")


def get_code():
    code, _ = open(os.path.join(project_path, "code")).read().split("\n")
    return code


@article("code", ret_val=get_code())
@pytest.mark.env(NEED_CODE="False")
@pytest.mark.env(CODE_EXPIRE_INTERVAL=30 * 24 * 3600)
@pytest.mark.asyncio
class TestArticle(object):

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_True(self):
        assert Article().right_code(get_code()) is True

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_False(self):
        assert Article().right_code("111111") is False

    async def test_check_code_off(self):
        assert Article().right_code("111111") is True

    async def test_build_sub_sql(self):
        kwargs = OrderedDict({"name": "john", "age": 15})
        sub, args = Article.build_sub_sql(kwargs, "des LIKE ? ", ["%red%"])
        assert sub == "des LIKE ?  AND name=? AND age=?"
        assert args == ["%red%", "john", 15]
        
    async def test_load(self):
        assert Article.load()