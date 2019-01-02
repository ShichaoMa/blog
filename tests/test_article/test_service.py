import pytest

from toolkit.settings import SettingsLoader
from pytest_apistellar import prop_alias

from blog.blog.article.service import ArticleService
arti_ser = prop_alias("blog.blog.article.service.ArticleService")


@pytest.mark.asyncio
class TestService(object):
    pytestmark = [
        arti_ser("settings", ret_val=SettingsLoader().load("settings")),
        ]
