# -*- coding:utf-8 -*-
import os

STATIC_FOLDER = os.environ.get("STATIC_FOLDER", "static")

STATIC_URL_PATH = os.environ.get("STATIC_URL_PATH", "/static")

TEMPLATE_FOLDER = os.environ.get("TEMPLATE_FOLDER", "templetes")

ES_HOST = os.environ.get("ES_HOST", "127.0.0.1:9200")

ES_USERNAME = os.environ.get("ES_USER", "elastic")

ES_PASSWORD = os.environ.get("ES_PASSWORD", "changeme")

INDEX = os.environ.get("INDEX", "blog")

DOC_TYPE = os.environ.get("DOC_TYPE", "articles")

USERNAME = os.environ.get("USERNAME", "test")

PASSWORD = os.environ.get("PASSWORD", "12345")

SECRET_KEY = os.urandom(24)

TIME_ZONE = os.environ.get("TIME_ZONE", 'Asia/Shanghai')

AUTHOR = os.environ.get("AUTHOR", "马式超")