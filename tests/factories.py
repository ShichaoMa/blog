import os

from apistellar import settings


def get_code():
    code, _ = open(os.path.join(
        settings["PROJECT_PATH"], "code")).read().split("\n")
    return code
