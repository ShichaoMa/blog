# -*- coding:utf-8 -*-
import os
import time
import pytz
import datetime

import shutil
from argparse import ArgumentParser
from elasticsearch import Elasticsearch


es = Elasticsearch("localhost:9200")

parser = ArgumentParser()

parser.add_argument("-p", "--path")
parser.add_argument("-a", "--author", default="马式超")
parser.add_argument("-f", "--feature", action="store_true")

parser.add_argument("tags", nargs="+")

args = vars(parser.parse_args())



id =time.strftime("%Y%m%d%H%M%S")
es.index("blog", "articles", id=id, body={
    "id": id,
    "tags": args["tags"],
    "description" :"先来个默认的",
    "title": os.path.basename(args["path"]).strip(".md"),
    "author": args["author"],
    "feature": args["feature"],
    "created_at": datetime.datetime.now(pytz.timezone('Asia/Shanghai')),
    "updated_at": datetime.datetime.now(pytz.timezone('Asia/Shanghai')),
})
shutil.copy(args["path"], "articles/%s.md"%id)