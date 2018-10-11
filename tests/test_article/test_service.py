import pytest

from toolkit.settings import SettingsLoader
from pytest_apistellar import prop_alias

from blog.blog.article.service import ArticleService
arti_ser = prop_alias("blog.blog.article.service.ArticleService")


@pytest.mark.usefixtures("mock")
@pytest.mark.asyncio
class TestService(object):
    pytestmark = [
        arti_ser("settings", ret_val=SettingsLoader().load("settings")),
        ]

    @arti_ser("code", ret_val="111111")
    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_True(self):
        assert ArticleService().check_code("111111") is True

    @arti_ser("code", ret_val="22222")
    @pytest.mark.env(NEED_CODE="True")
    async def test_check_code_on_False(self):
        assert ArticleService().check_code("111111") is False

    @arti_ser("code", ret_val="3333")
    @pytest.mark.env(NEED_CODE="False")
    async def test_check_code_off(self):
        assert ArticleService().check_code("111111") is True