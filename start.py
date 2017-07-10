# -*- coding:utf-8 -*-
import os
import re
import json
import pytz
import sqlite3
import markdown
import datetime
import elasticsearch

from threading import local
from flask import Flask, render_template, request, session, url_for, redirect

local = local()
project_path = os.path.dirname(__file__)
app = Flask(__name__)
app.config.from_pyfile(os.path.join(project_path, "settings.py"))
app.static_folder = app.config.get("STATIC_FOLDER")
app.static_url_path = app.config.get("STATIC_URL_PATH")
app.template_folder = app.config.get("TEMPLATE_FOLDER")
tz = pytz.timezone(app.config.get("TIME_ZONE"))


def conn_wrapper(func):
    """
    sqlite的conn不能多个线程使用
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        self = args[0]
        index = args[1]
        if self.config.get("DB", "ES") != "ES":
            self.conn = getattr(local, "conn", None)
            if not self.conn:
                self.conn = sqlite3.connect(os.path.join(project_path, "db", index))
                self.cur = self.conn.cursor()
        result = func(*args, **kwargs)
        if self.config.get("DB", "ES") != "ES":
            self.conn.commit()
            # self.cur.close()
            # self.conn.close()
        return result
    return wrapper


def decode(buffer):
    try:
        return buffer.decode("utf-8")
    except UnicodeDecodeError:
        return buffer.decode("gbk")


def format_data(data):
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


class DB:

    def __init__(self, config):
        self.config = config
        if config.get("DB", "ES") == "ES":
            self.table_initialize = open(os.path.join(project_path, "blog.json")).read()
            self.conn = elasticsearch.Elasticsearch(config.get("ES_HOST"), http_auth=(config.get("ES_USERNAME"), config.get("ES_PASSWORD")))
            self.conn.indices.create(config.get("INDEX"), body=json.loads(self.table_initialize), ignore=400)

        else:
            os.makedirs(os.path.join(project_path, "db"), exist_ok=True)
            self.table_initialize = open(os.path.join(project_path, "blog.sql")).read()
            self.conn = sqlite3.connect(os.path.join(project_path, "db", config.get("INDEX")))
            self.cur = self.conn.cursor()
            try:
                self.cur.execute(self.table_initialize)
            except sqlite3.OperationalError as e:
                pass
            finally:
                self.cur.close()
                self.conn.close()

    @conn_wrapper
    def index(self, inde, doc_type, id, body):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.index(inde, doc_type, id=id, body=body)
        else:
            self.cur.execute("INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);".format(doc_type), (
                id, body["description"], ",".join(body["tags"]), body["article"], body["author"], body["title"],
            1 if body["feature"] else 0, int(body["created_at"].timestamp()), int(body["updated_at"].timestamp()), body["show"]))

    @conn_wrapper
    def get(self, index, doc_type, id):
        if self.config.get("DB", "ES") == "ES":
            data = self.conn.get(index, id=id, doc_type=doc_type, ignore=404)
            if data["found"]:
                return data
        else:
            self.cur.execute("SELECT * FROM {} WHERE id=?;".format(doc_type), (id, ))
            data = self.cur.fetchone()
            if data:
                return format_data(data)
        return ""

    @conn_wrapper
    def update(self, index, doc_type, id, body):
        if self.config.get("DB", "ES") == "ES":
            return self.conn.update(index, doc_type, id=id, body=body)
        else:
            self.cur.execute("UPDATE {} SET description=?, tags=?, article=?, author=?,"
                             " title=?, feature=?, updated_at=? WHERE id=?;".format(doc_type), (
                body["doc"]["description"], ",".join(body["doc"]["tags"]), body["doc"]["article"],
                body["doc"]["author"], body["doc"]["title"], 1 if body["doc"]["feature"] else 0,
                int(body["doc"]["updated_at"].timestamp()), id
            ))
            self.conn.commit()

    @conn_wrapper
    def delete(self, index, doc_type, id):
        if self.config.get("DB", "ES") == "ES":
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "id": id
                                }
                            },
                            {
                                "term": {
                                    "show": 1
                                }
                            }
                        ]
                    }
                }
            }
            return self.conn.delete_by_query(index, doc_type=doc_type, body=body)
        else:
            self.cur.execute("DELETE FROM %s WHERE show=1 and id='%s';"%(doc_type, id))
            self.conn.commit()

    @conn_wrapper
    def search(self, index, doc_type, search_field, _from, size):
        if self.config.get("DB", "ES") == "ES":
            condition = {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "_all": search_field
                                }
                            },
                            {
                                "term": {
                                    "show": 1
                                }
                            }
                        ]
                    }
            } if search_field else {
                                "term": {
                                    "show": 1
                                }
                            }
            body = {
                "query": condition,
                "from": _from,
                "size": size,
                "sort": {
                    "updated_at": "desc"
                }
            }
            data = self.conn.search(index=index, doc_type=doc_type, body=body)
            condition["bool"]["must"].append({
                "term": {
                    "feature": True
                }
            })
            return data["hits"]["total"], data["hits"]["hits"], \
                   self.conn.search(index=index, doc_type=doc_type, body=body)["hits"]["hits"]
        else:
            sub = "AND article LIKE '%%%s%%'"%search_field if search_field else ""
            self.cur.execute("SELECT * FROM %s WHERE show=1 %s ORDER BY updated_at desc limit %s offset %s;"%(
                doc_type, sub, size, _from))
            rs = self.cur.fetchall()
            self.cur.execute("SELECT COUNT(id) FROM {}".format(doc_type))
            count = self.cur.fetchone()[0]
            self.cur.execute("SELECT * FROM %s WHERE show=1 AND feature=1 %s ORDER BY updated_at desc limit %s offset %s;" % (
                                 doc_type, sub, size, _from))
            return count, [format_data(data) for data in rs], [format_data(data) for data in self.cur.fetchall()]

    @conn_wrapper
    def gen_article(self, index, doc_type, id):
        if not id:
            return ""
        if self.config.get("DB", "ES") == "ES":
            data = self.conn.get(index, id=id, doc_type=doc_type)
            if data["found"]:
                return data["_source"]["article"]
        else:
            self.cur.execute("SELECT article FROM %s WHERE id='%s';"%(doc_type, id))
            data = self.cur.fetchone()
            if data:
                return data[0]
        return ""


db = DB(app.config)


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
                               article=db.gen_article(app.config.get("INDEX"), app.config.get("DOC_TYPE"), request.form.get("id")))
    else:
        return render_template("login.html", title=request.form.get("title", ""),
                               tags=request.form.get("tags", ""),
                               description=request.form.get("description", ""),
                               author=request.form.get("author", ""),
                               feature=request.form.get("feature"),
                               id=request.form.get("id", ""),
                               ref=ref)


@app.route("/imports", methods=["post"])
def imports():
    if not session.get("login"):
        return render_template("login.html", ref="imports")
    file = request.files["article"]
    title = request.form.get("title")
    article = decode(file.read())
    author = request.form.get("author") or app.config.get("AUTHOR")
    tags = request.form.get("tags").split(",")
    feature = eval(request.form.get("feature", "False"))
    description = request.form.get("description")
    id = datetime.datetime.now(tz).strftime("%Y%m%d%H%M%S")
    body = {
        "id": id,
        "tags": tags,
        "description": description,
        "title": title or file.filename.replace(".md", ""),
        "article": article,
        "author": author,
        "feature": feature,
        "created_at": datetime.datetime.now(tz),
        "updated_at": datetime.datetime.now(tz),
        "show": 1,
    }
    db.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    return render_template("imports.html", success="success")


@app.route("/edit")
def edit():
    id = request.args.get("id")
    doc = db.get(app.config.get("INDEX"), id=id, doc_type=app.config.get("DOC_TYPE"))
    doc["_source"]["tags"] = ",".join(doc["_source"]["tags"])
    if not session.get("login"):
        return render_template("login.html", ref="edit", **doc["_source"])
    return render_template("edit.html", ref="update", **doc["_source"])


@app.route("/update", methods=["post"])
def update():
    if not session.get("login"):
        return render_template("login.html", ref="imports")
    article = request.form.get("article")
    id = request.form.get("id")
    title = request.form.get("title")
    author = request.form.get("author") or app.config.get("AUTHOR")
    tags = request.form.get("tags").split(",")
    feature = eval(request.form.get("feature", "False"))
    description = request.form.get("description")
    body = {
        "doc": {
            "tags": tags,
            "description": description,
            "title": title,
            "article": article,
            "author": author,
            "feature": feature,
            "updated_at": datetime.datetime.now(tz),
        }
    }
    db.update(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    return redirect(url_for("index"))


@app.route("/delete")
def delete():
    if not session.get("login"):
        return render_template("login.html", ref="delete", id=request.args.get("id", ""))
    db.delete(app.config.get("INDEX"), id=request.args.get("id"), doc_type=app.config.get("DOC_TYPE"))
    return redirect(url_for("index"))


@app.route("/article")
def article():
    article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), request.args.get("id"))
    format_article_body = markdown.markdown(article["_source"]["article"], extensions=['markdown.extensions.extra'])
    _, articles = format_articles([article])
    article = articles[0]
    article["article"] = format_article_body
    return json.dumps(article)


@app.route("/me")
def me():
    id = "me"
    article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id)
    if article:
        article = article["_source"]
    else:
        created_at = datetime.datetime.now(tz)
        article = {"id": id,
               "author": app.config.get("AUTHOR"),
               "tags": [id],
               "description": id,
               "feature": 0,
               "article": id,
               "title": id,
               "show": 0,
               "updated_at": created_at,
               "created_at": created_at}
        db.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id, article)
        article["updated_at"] = created_at.strftime("%Y-%m-%dT%H:%M:%S")
        article["created_at"] = created_at.strftime("%Y-%m-%dT%H:%M:%S")
    article["article"] = markdown.markdown(article["article"],
                                        extensions=['markdown.extensions.extra'])
    del article["article"]
    return json.dumps(article)


@app.route("/contact")
def contact():
    id = "contact"
    article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id)
    if article:
        article = article["_source"]
    else:
        created_at = datetime.datetime.now(tz)
        article = {"id": id,
                   "author": app.config.get("AUTHOR"),
                   "tags": [id],
                   "description": id,
                   "feature": 0,
                   "article": id,
                   "title": id,
                   "show": 0,
                   "updated_at": created_at,
                   "created_at": created_at}
        db.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id, article)
        article["updated_at"] = created_at.strftime("%Y-%m-%dT%H:%M:%S")
        article["created_at"] = created_at.strftime("%Y-%m-%dT%H:%M:%S")
    article["article"] = markdown.markdown(article["article"],
                                        extensions=['markdown.extensions.extra'])
    del article["article"]

    return json.dumps(article)


def format_articles(articles):
    tags = {}
    format_articles = []
    for article in articles:
        article = article["_source"]
        mth = re.search(r"\!\[.*?\]\((.*?)\)", article.pop("article"))
        article["first_img"] = mth.group(1) if mth else ""
        for tag in article["tags"]:
            tags[tag.upper()] = tags.setdefault(tag.upper(), 0) + 1
        format_articles.append(article)
    return tags, format_articles


@app.route("/show")
def show():
    count, articles, feature_articles = db.search(app.config.get("INDEX"), app.config.get("DOC_TYPE"),
                         request.args.get("searchField"), request.args.get("from", 0),
                         request.args.get("size", 10))
    tags, articles = format_articles(articles)
    _, feature_articles = format_articles(feature_articles)
    return json.dumps({"count": count, "articles": articles, "feature_articles": feature_articles,
                       "tags": [i[0] for i in sorted(tags.items(), key=lambda x: x[1], reverse=True)]})


if __name__ == "__main__":
    app.run(debug=eval(os.environ.get("DEBUG", "False")),
            processes=int(os.environ.get("PROCESSES", 1)),
            threaded=eval(os.environ.get("THREADED", "False")),
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)))
