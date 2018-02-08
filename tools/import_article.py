import re
import sys
import glob
import time
import pytz
import datetime

from flask import Flask
from os.path import dirname, join, basename, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))

from blog.db import DataBase
from blog.utils import project_path

app = Flask(__name__)
app.config.from_pyfile(join(project_path, "settings.py"))
tz = pytz.timezone(app.config.get("TIME_ZONE"))

db = DataBase(app.config)


def retrieve(word, article):
    regex = re.compile(r"\[comment\]: <%s> \((.+?)\)" % word)
    for line in article[:]:
        mth = regex.search(line)
        if mth:
            article.remove(line)
            return mth.group(1)
    return ""


def insert(filename):
    id = time.strftime("%Y%m%d%H%M%S")
    title = basename(filename).replace(".md", "")
    if not db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), title=title):
        article = open(filename).readlines()
        body = {
            "id": id,
            "tags": retrieve("tags", article).split(","),
            "description": retrieve("description", article),
            "title": retrieve("title", article) or title,
            "author": retrieve("author", article) or "夏洛之枫",
            "article": "".join(article),
            "feature": 0,
            "created_at": datetime.datetime.now(tz),
            "updated_at": datetime.datetime.now(tz),
            "show": 1,
        }
        db.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
        time.sleep(1)


def main():
    for filename in glob.glob(join(sys.argv[1], "*")):
        insert(filename)


if __name__ == "__main__":
    main()
