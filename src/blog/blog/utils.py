# -*- coding:utf-8 -*-
import os
import time
import pytz
import random
import datetime

from apistellar import settings
default_tz = pytz.timezone('Asia/Shanghai')


def decode(buffer):
    try:
        return buffer.decode("utf-8")
    except UnicodeDecodeError:
        return buffer.decode("gbk")


def code_generator(interval, key="ABCDEFGHIGKLMNOPQISTUVWXYZ0123456789"):
    project_path = settings["PROJECT_PATH"]
    try:
        code, last_time = open(os.path.join(
            project_path, "code")).read().split("\n")
        last_time = int(last_time)
    except OSError:
        last_time = 0
    while True:
        if time.time() - last_time > interval:
            code, last_time = "".join(random.choices(key, 6)), time.time()
            with open(os.path.join(project_path, "code"), "w") as f:
                f.write(code)
                f.write("\n%d" % time.time())
        yield code


def get_id():
    return datetime.datetime.now(default_tz).strftime("%Y%m%d%H%M%S")


def now(tz=None):
    return datetime.datetime.now(tz or default_tz)
