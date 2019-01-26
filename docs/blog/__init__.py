# blog API
from .welcome import Welcome
from .article import Article


class Blog(Welcome, Article):
    pass