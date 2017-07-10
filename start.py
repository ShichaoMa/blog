# -*- coding:utf-8 -*-
import os
import sys
import json
import pytz
import codecs
import markdown
import datetime
import sqlite3

from io import StringIO
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, session, url_for, redirect

project_path = os.path.dirname(__file__)
app = Flask(__name__)
app.config.from_pyfile(os.path.join(project_path, "settings.py"))
app.static_folder = app.config.get("STATIC_FOLDER")
app.static_url_path = app.config.get("STATIC_URL_PATH")
app.template_folder = app.config.get("TEMPLATE_FOLDER")
tz = pytz.timezone(app.config.get("TIME_ZONE"))


def conn_wrapper(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        index = args[1]
        if self.config.get("DB", "ES") != "ES":
            self.conn = sqlite3.connect(os.path.join(project_path, "db", index))
            self.cur = self.conn.cursor()
        result = func(*args, **kwargs)
        if self.config.get("DB", "ES") != "ES":
            self.cur.close()
            self.conn.close()
        return result
    return wrapper


class DB:

    def __init__(self, config):
        self.config = config
        if config.get("DB", "ES") == "ES":
            self.conn = Elasticsearch(config.get("ES_HOST"), http_auth=(config.get("ES_USERNAME"), config.get("ES_PASSWORD")))
        else:
            os.makedirs(os.path.join(project_path, "db"), exist_ok=True)
            self.conn = sqlite3.connect(os.path.join(project_path, "db", config.get("INDEX")))
            self.cur = self.conn.cursor()
            try:
                self.cur.execute("""
                CREATE TABLE %s(
                   ID CHAR(14) PRIMARY KEY     NOT NULL,
                   DESCRIPTION           TEXT    NOT NULL,
                   TAGS            TEXT     NOT NULL,
                   AUTHOR        CHAR(20)     NOT NULL,
                   TITLE        CHAR(50)     NOT NULL,
                   FEATURE      INT      NOT NULL,
                   CREATED_AT         INT     NOT NULL,
                   UPDATED_AT         INT     NOT NULL
                );
                """%(self.config.get("DOC_TYPE")))
            except sqlite3.OperationalError as e:
                print(e)
            finally:
                self.cur.close()
                self.conn.close()

    @conn_wrapper
    def exists(self, index, doc_type, id):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.exists(index, doc_type, id)
        else:
            self.cur.execute("SELECT ID FROM %s WHERE ID=%s"%(doc_type, id))
            result = self.cur.fetchall()
            if result:
                return True
            else:
                return False

    @conn_wrapper
    def index(self, inde, doc_type, id, body):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.index(inde, doc_type, id=id, body=body)
        else:
            self.conn = sqlite3.connect(os.path.join(project_path, "db", inde))
            self.cur = self.conn.cursor()
            self.cur.execute("INSERT INTO %s VALUES('%s', '%s', '%s', '%s', '%s', %s, %s, %s);" % (
                doc_type, id, body["description"], ",".join(body["tags"]), body["author"], body["title"],
            1 if body["feature"] else 0, int(body["created_at"].timestamp()), int(body["updated_at"].timestamp())))
            self.conn.commit()

    @conn_wrapper
    def get(self, index, doc_type, id):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.get(index, id=id, doc_type=doc_type)
        else:
            self.cur.execute("SELECT * FROM %s WHERE id='%s';"%(doc_type, id))
            data = self.cur.fetchone()
            return {"_source": {
                "id": data[0],
                "description": data[1],
                "tags": data[2].split(","),
                "author": data[3],
                "title": data[4],
                "feature": bool(data[5]),
                "created_at": datetime.datetime.fromtimestamp(data[6], tz).strftime("%Y-%m-%dT%H:%M:%S"),
                "updated_at": datetime.datetime.fromtimestamp(data[7], tz).strftime("%Y-%m-%dT%H:%M:%S")
            }}

    @conn_wrapper
    def update(self, index, doc_type, id, body):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.update(index, doc_type, id=id, body=body)
        else:
            self.cur.execute("UPDATE %s SET description='%s', tags='%s', author='%s', title='%s', feature=%s, created_at=%s, updated_at=%s;"%( doc_type,
                body["doc"]["description"], ",".join(body["doc"]["tags"]), body["doc"]["author"], body["doc"]["title"], 1 if body["doc"]["feature"] else 0,
                int(body["doc"]["created_at"].timestamp()), int(body["doc"]["updated_at"].timestamp())
            ))
            self.conn.commit()

    @conn_wrapper
    def delete(self, index, doc_type, id):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.delete(index, doc_type=doc_type, id=id)
        else:
            self.cur.execute("DELETE FROM %s WHERE id='%s';"%(doc_type, id))
            self.conn.commit()

    @conn_wrapper
    def search(self, index, doc_type, body):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.search(index=index, doc_type=doc_type, body=body)["hits"]["hits"]
        else:
            sub = "and tags like '%%%s%%'"%body["query"]["match"]["_all"] if body["query"] else ""
            self.cur.execute("SELECT * FROM %s WHERE 1=1 %s limit %s offset %s;"%(
                doc_type, sub, body["size"], body["from"]))
            rs = self.cur.fetchall()
            return [{"_source": {
                "id": data[0],
                "description": data[1],
                "tags": data[2].split(","),
                "author": data[3],
                "title": data[4],
                "feature": bool(data[5]),
                "created_at": datetime.datetime.fromtimestamp(data[6], tz).strftime("%Y-%m-%dT%H:%M:%S"),
                "updated_at": datetime.datetime.fromtimestamp(data[7], tz).strftime("%Y-%m-%dT%H:%M:%S")
            }}for data in rs]


db = DB(app.config)


class CustomIO(StringIO):

    def save(self, filename):
        open(filename, "w").write(self.read())
        self.close()


def gen_article(id):
    try:
        if id:
            input_file = codecs.open(os.path.join(project_path, "articles", "%s.md" % id), mode="r",
                                     encoding="utf-8")
            return input_file.read()
    except UnicodeDecodeError:
        input_file = codecs.open(os.path.join(project_path, "articles", "%s.md" % id), mode="r",
                                 encoding="gbk")
        return input_file.read()
    except Exception:
        pass
    return ""


@app.route("/")
def index():
    return render_template('index.html', author=app.config.get("AUTHOR"))


@app.route("/import")
def login():
    if not session.get("login"):
        return render_template("login.html", ref="imports")
    else:
        return render_template("imports.html", success="",
                               title=request.form.get("title", ""),
                               tags=request.form.get("tags", ""),
                               description=request.form.get("description", ""),
                               author=request.form.get("author", ""),
                               feature=request.form.get("feature"),
                               id=request.form.get("id", ""))


@app.route('/check', methods=["post"])
def check():
    ref = request.form.get("ref")
    if request.form.get("username") == app.config.get("USERNAME") and request.form.get("password") == app.config.get("PASSWORD"):
        session["login"] = "%s:%s"%(request.form.get("username"), request.form.get("password"))
        return render_template("%s.html"%ref, success="",
                               title=request.form.get("title", ""),
                               tags=request.form.get("tags", ""),
                               description=request.form.get("description", ""),
                               author=request.form.get("author", ""),
                               feature=request.form.get("feature"),
                               id=request.form.get("id", ""),
                               ref=ref,
                               article=gen_article(request.form.get("id")))
    else:
        return render_template("login.html", ref="ref")


@app.route("/imports", methods=["post"])
def imports():
    if not session.get("login"):
        return render_template("login.html", ref="imports")
    file = request.files["article"]
    title = request.form.get("title")
    author = request.form.get("author") or app.config.get("AUTHOR")
    tags = request.form.get("tags").split(",")
    feature = True if request.form.get("feature") == "True" else False
    description = request.form.get("description")
    id = datetime.datetime.now(tz).strftime("%Y%m%d%H%M%S")
    body = {
        "id": id,
        "tags": tags,
        "description": description,
        "title": title or file.filename.replace(".md", ""),
        "author": author,
        "feature": feature,
        "created_at": datetime.datetime.now(tz),
        "updated_at": datetime.datetime.now(tz),
    }
    if db.exists(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id):
        body.pop("created_at")
    db.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    file.save(os.path.join(project_path, "articles/%s.md"%id))
    return render_template("imports.html", success="success")


@app.route("/edit")
def edit():
    id = request.args.get("id")
    try:
        doc = db.get(app.config.get("INDEX"), id=id, doc_type=app.config.get("DOC_TYPE"))
    except Exception:
        doc = {}
    if not doc:
        doc["_source"] = {}
        doc["_source"]["id"] = id
        doc["_source"]["tags"] = [id]
        doc["_source"]["feature"] = False
        doc["_source"]["description"] = id
        doc["_source"]["author"] = ""
        doc["_source"]["title"] = id
    doc["_source"]["tags"] = ",".join(doc["_source"]["tags"])
    if not session.get("login"):
        return render_template("login.html", ref="edit", **doc["_source"])
    return render_template("edit.html", ref="update", article=gen_article(id), **doc["_source"])


@app.route("/update", methods=["post"])
def update():
    if not session.get("login"):
        return render_template("login.html", ref="imports")
    file = CustomIO(request.form.get("article"))
    id = request.form.get("id")
    title = request.form.get("title")
    author = request.form.get("author") or app.config.get("AUTHOR")
    tags = request.form.get("tags").split(",")
    feature = True if request.form.get("feature") == 1 else False
    description = request.form.get("description")
    body = {
        "doc": {
            "tags": tags,
            "description": description,
            "title": title,
            "author": author,
            "feature": feature,
            "updated_at": datetime.datetime.now(tz),
        }
    }
    try:
        db.update(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    except Exception:
        pass
    file.save(os.path.join(project_path, "articles/%s.md" % id))
    return redirect(url_for("index"))


@app.route("/delete")
def delete():
    if not session.get("login"):
        return render_template("login.html", ref="delete", id=request.args.get("id", ""))
    try:
        db.delete(app.config.get("INDEX"), id=request.args.get("id"), doc_type=app.config.get("DOC_TYPE"))
    except Exception:
        pass
    try:
        os.unlink(os.path.join("articles", "%s.md" % request.args.get("id")))
    except FileNotFoundError:
        pass
    return redirect(url_for("index"))


@app.route("/article")
def article():
    return json.dumps({"body": markdown.markdown(gen_article(request.args.get("id")), extensions=['markdown.extensions.extra'])})


@app.route("/me")
def me():
    body = markdown.markdown(gen_article("我的自我介绍"), extensions=['markdown.extensions.extra'])
    if not body:
        created_at = datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")
    else:
            created_at = datetime.datetime.fromtimestamp(os.stat(os.path.join(project_path, "articles", "我的自我介绍.md")).st_ctime, tz).strftime("%Y-%m-%dT%H:%M:%S")
    return json.dumps({"author":app.config.get("AUTHOR"),
                       "body": body,
                       "title": "我的自我介绍",
                       "created_at": created_at})


@app.route("/contact")
def contact():
    body = markdown.markdown(gen_article("我的联系方式"), extensions=['markdown.extensions.extra'])
    if not body:
        created_at = datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")
    else:
        created_at = datetime.datetime.fromtimestamp(
            os.stat(os.path.join(project_path, "articles", "我的联系方式.md")).st_ctime, tz).strftime("%Y-%m-%dT%H:%M:%S")
    return json.dumps({"author": app.config.get("AUTHOR"),
                       "body": body,
                       "title": "我的联系方式",
                       "created_at": created_at})


@app.route("/show")
def show():
    condition = {
                "match": {
                    "_all": request.args.get("searchField")
                }
            } if request.args.get("searchField") else {}
    articles = db.search("blog", doc_type="articles", body={
            "query": condition,
            "from": request.args.get("from", 0),
            "size": request.args.get("size", 10),
        })
    tags = {}
    format_articles = []
    for article in articles:
        article = article["_source"]
        for tag in article["tags"]:
            tags[tag.upper()] = tags.setdefault(tag.upper(), 0) + 1
        format_articles.append(article)
    return json.dumps({"articles": format_articles, "tags": [i[0] for i in sorted(tags.items(), key=lambda x: x[1], reverse=True)]})


if __name__ == "__main__":
    app.run(debug=eval(os.environ.get("DEBUG", "False")),
            processes=int(os.environ.get("PROCESSES", 1)),
            threaded=eval(os.environ.get("THREADED", "False")),
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)))
