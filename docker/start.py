# -*- coding:utf-8 -*-
import os
import json
import pytz
import codecs
import markdown
import datetime

from io import StringIO
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, session, url_for, redirect

project_path = os.path.dirname(__file__)
app = Flask(__name__)
app.config.from_pyfile(os.path.join(project_path, "settings.py"))
app.static_folder = app.config.get("STATIC_FOLDER")
app.static_url_path = app.config.get("STATIC_URL_PATH")
app.template_folder = app.config.get("TEMPLATE_FOLDER")
es = Elasticsearch(app.config.get("ES_HOST"), http_auth=(app.config.get("ES_USERNAME"), app.config.get("ES_PASSWORD")))
tz = pytz.timezone('Asia/Shanghai')

class CustomIO(StringIO):

    def save(self, filename):
        open(filename, "w").write(self.read())
        self.close()


def gen_article(id):
    if id:
        input_file = codecs.open(os.path.join(project_path, "articles", "%s.md" % id), mode="r",
                                 encoding="utf-8")
        return input_file.read()
    return ""


@app.route("/")
def index():
    return render_template('index.html')


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
    if request.form.get("username") == app.config.get("USERNAME", "test") and request.form.get("password") == app.config.get("PASSWORD", "12345"):
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
        return render_template("login.html", ref="import")
    file =request.files["article"]
    title = request.form.get("title")
    author = request.form.get("author") or "马式超"
    tags = request.form.get("tags").split(",")
    feature = True if request.form.get("feature") == "True" else False
    description = request.form.get("description")
    id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    body = {
        "id": id,
        "tags": tags,
        "description": description,
        "title": title or file.filename.strip(".md"),
        "author": author,
        "feature": feature,
        "created_at": datetime.datetime.now(tz),
        "updated_at": datetime.datetime.now(tz),
    }
    if es.exists(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id):
        body.pop("created_at")
    es.index(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    file.save(os.path.join(project_path, "articles/%s.md"%id))
    return render_template("imports.html", success="success")


@app.route("/edit")
def edit():
    id = request.args.get("id")
    try:
        doc = es.get(app.config.get("INDEX"), id=id, doc_type=app.config.get("DOC_TYPE"))
    except Exception as e:
        print(e)
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
        return render_template("login.html", ref="import")
    file = CustomIO(request.form.get("article"))
    id = request.form.get("id")
    title = request.form.get("title")
    author = request.form.get("author") or "马式超"
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
            "updated_at": datetime.datetime.now(pytz.timezone('Asia/Shanghai')),
        }
    }
    try:
        es.update(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    except Exception as e:
        print(e)
    file.save(os.path.join(project_path, "articles/%s.md" % id))
    return redirect(url_for("index"))


@app.route("/delete")
def delete():
    if not session.get("login"):
        return render_template("login.html", ref="delete", id=request.args.get("id", ""))
    try:
        es.delete(app.config.get("INDEX"), id=request.args.get("id"), doc_type=app.config.get("DOC_TYPE"))
        os.unlink(os.path.join("articles", "%s.md" % request.args.get("id")))
    except Exception:
        pass
    return redirect(url_for("index"))


@app.route("/artile")
def artile():
    return json.dumps({"body": markdown.markdown(gen_article(request.args.get("id")), extensions=['markdown.extensions.extra'])})


@app.route("/me")
def me():
    return json.dumps({"author":"马式超",
                       "body": markdown.markdown(gen_article("我的自我介绍"), extensions=['markdown.extensions.extra']),
                       "title": "我的自我介绍",
                       "created_at": "2017-07-08T12:12:12"})


@app.route("/contact")
def contact():
    return json.dumps({"author":"马式超",
                       "body": markdown.markdown(gen_article("我的联系方式"), extensions=['markdown.extensions.extra']),
                       "title": "我的联系方式",
                       "created_at": "2017-07-08T12:12:12"})


@app.route("/show")
def show():
    condition = {
                "match": {
                    "_all": request.args.get("searchField")
                }
            } if request.args.get("searchField") else {}
    articles = es.search(index="blog", doc_type="articles", body={
            "query": condition,
            "from": request.args.get("from", 0),
            "size": request.args.get("size", 10),
        })["hits"]["hits"]
    tags = {}
    format_articles = []
    for article in articles:
        article = article["_source"]
        for tag in article["tags"]:
            tags[tag.upper()] = tags.setdefault(tag.upper(), 0) + 1
        format_articles.append(article)
    return json.dumps({"articles": format_articles, "tags": [i[0] for i in sorted(tags.items(), key=lambda x: x[1], reverse=True)]})


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))