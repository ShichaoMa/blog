import pytest

from pytest_apistellar import prop_alias
from toolkit.settings import SettingsLoader

from blog.blog.article.article import Article


article = prop_alias("blog.blog.article.article.Article")


@pytest.mark.asyncio
class TestArticle(object):
    pytestmark = [
        article("code", ret_val="111111"),
        ]

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_True(self):
        assert Article().right_code("111111") is True

    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_False(self):
        assert Article().right_code("111111") is False

    @pytest.mark.env(NEED_CODE="False")
    async def test_check_code_off(self):
        assert Article().right_code("111111") is True