# -*- coding:utf-8 -*-
import os
import time
import random

from apistellar import settings


def code_generator(interval):
    project_path = settings["PROJECT_PATH"]
    code = None

    try:
        code, last_time = get_stored_code(project_path)
    except OSError:
        last_time = 0

    while True:
        pair = gen_code(last_time, interval, project_path)
        if pair:
            code = pair[0]
            last_time = pair[1]
        yield code


def gen_code(last_time, interval, project_path):
    key = "ABCDEFGHIGKLMNOPQISTUVWXYZ0123456789"

    if time.time() - last_time > interval:
        code, last_time = "".join(random.choices(key, k=6)), time.time()
        with open(os.path.join(project_path, "code"), "w") as f:
            f.write(code)
            f.write("\n%d" % time.time())
        return code, int(last_time)
    return None


def get_stored_code(project_path):
    code, last_time = open(os.path.join(project_path, "code")).read().split("\n")
    last_time = int(last_time)
    return code, last_time
