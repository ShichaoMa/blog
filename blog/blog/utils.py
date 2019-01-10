# -*- coding:utf-8 -*-
import re
import os
import time
import pytz
import random
import sqlite3
import hashlib
import datetime

from threading import local


local = local()
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
default_tz = pytz.timezone('Asia/Shanghai')


def decode(buffer):
    try:
        return buffer.decode("utf-8")
    except UnicodeDecodeError:
        return buffer.decode("gbk")


def format_data(data, tz):
    return {"_source": {
        "id": data[0],
        "description": data[1],
        "tags": data[2].split(","),
        "article": data[3],
        "author": data[4],
        "title": data[5],
        "feature": bool(data[6]),
        "created_at": datetime.datetime.fromtimestamp(data[7], tz).strftime("%Y-%m-%dT%H:%M:%S"),
        "updated_at": datetime.datetime.fromtimestamp(data[8], tz).strftime("%Y-%m-%dT%H:%M:%S")
    }}


def format_articles(articles, tags=None):
    group_tags = {}
    formatted = []
    for article in articles:
        article["first_img"] = get_image(article.pop("article"))
        if not tags:
            for tag in article["tags"]:
                group_tags[tag.upper()] = group_tags.setdefault(tag.upper(), 0) + 1
        formatted.append(article)

    if tags:
        for ts in tags:
            for tag in ts.split(","):
                group_tags[tag.upper()] = group_tags.setdefault(tag.upper(), 0) + 1
    return group_tags, formatted


def get_image(body):
    try:
        image_part = body[:body.index("\n")]
    except ValueError:
        image_part = body
    mth = re.search(r"!\[.*?\]\((.*?)\)", image_part)
    return mth.group(1) if mth else ""


def code_generator(interval, key="ABCDEFGHIGKLMNOPQISTUVWXYZ0123456789"):
    try:
        code, last_time = open(os.path.join(project_path, "code")).read().split("\n")
        last_time = int(last_time)
    except OSError:
        last_time = 0
    while True:
        if time.time() - last_time > interval:
            code, last_time = "".join(random.choice(key) for i in range(6)), time.time()
            with open(os.path.join(project_path, "code"), "w") as f:
                f.write(code)
                f.write("\n%d"%time.time())
        yield code


def get_cut_file_name(project_path, url, top, left, width, height):
    sh = hashlib.sha1(url.encode())
    sh.update(bytes(str(top), encoding="utf-8"))
    sh.update(bytes(str(left), encoding="utf-8"))
    sh.update(bytes(str(width), encoding="utf-8"))
    sh.update(bytes(str(height), encoding="utf-8"))
    name = sh.hexdigest()[:10] + ".png"
    return os.path.join(project_path, "static/temp/", name)


def get_id():
    return datetime.datetime.now(default_tz).strftime("%Y%m%d%H%M%S")


def now(tz=None):
    return datetime.datetime.now(tz or default_tz)
