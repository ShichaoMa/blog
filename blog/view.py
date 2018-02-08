# -*- coding:utf-8 -*-
import os
import re
import json
import pytz
import zipfile
import markdown
import datetime
import html2text

from io import BytesIO
from flask import Flask, render_template, \
    request, session, url_for, redirect, make_response

from .db import DataBase
from .html_cut import Cuter
from .utils import project_path, decode, format_articles, \
    code_generator, get_image, get_cut_file_name

app = Flask("blog")
app.config.from_pyfile(os.path.join(project_path, "settings.py"))
app.static_folder = os.path.join(project_path, app.config.get("STATIC_FOLDER"))
app.static_url_path = app.config.get("STATIC_URL_PATH")
app.template_folder = os.path.join(project_path, app.config.get("TEMPLATE_FOLDER"))
tz = pytz.timezone(app.config.get("TIME_ZONE"))
cuter = Cuter(app.config.get("PHANTOMJS_PATH"), os.path.join(project_path, "cut_html.js"))

db = DataBase(app.config)
code_generator = code_generator(app.config.get("CODE_EXPIRE_INTERVAL", 60*60*24*7))
next(code_generator)


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
    if request.form.get("username") == app.config.get("USERNAME") and \
                    request.form.get("password") == app.config.get("PASSWORD"):

        session["login"] = "%s:%s" % (request.form.get("username"), request.form.get("password"))
        return render_template("%s.html"%ref, success="",
                               title=request.form.get("title", ""),
                               tags=request.form.get("tags", ""),
                               description=request.form.get("description", ""),
                               author=request.form.get("author", ""),
                               feature=request.form.get("feature"),
                               id=request.form.get("id", ""),
                               ref=ref,
                               article=db.gen_article(
                                   app.config.get("INDEX"), app.config.get("DOC_TYPE"), request.form.get("id")))
    else:
        return render_template("login.html", title=request.form.get("title", ""),
                               tags=request.form.get("tags", ""),
                               description=request.form.get("description", ""),
                               author=request.form.get("author", ""),
                               feature=request.form.get("feature"),
                               id=request.form.get("id", ""),
                               ref=ref)


@app.route('/load')
def load():
    if request.args.get("username") == app.config.get("USERNAME") and \
                    request.args.get("password") == app.config.get("PASSWORD"):
        session["login"] = "%s:%s"%(request.form.get("username"), request.form.get("password"))
        return json.dumps({"result": 1})
    else:
        return json.dumps({"result": 0})


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


@app.route("/export")
def export():
    ids = request.args.get("ids")
    if ids:
        ids = ids.split(",")
        articles = []
    else:
        ids = []
        count, articles, feature_articles = db.search(
            app.config.get("INDEX"), app.config.get("DOC_TYPE"),
            request.args.get("searchField"),
            request.args.get("from", 0),
            request.args.get("size", 20))
    zip_file = BytesIO()
    zf = zipfile.ZipFile(zip_file, "w")
    try:
        buffer = None
        for id in ids:
            article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id)
            ext = "md"
            if id == "me":
                if request.args.get("code") != next(code_generator) or not article:
                    return json.dumps({"error": True})
                from html.parser import unescape
                from weasyprint import HTML, Attachment
                from urllib.parse import urlparse, urljoin
                html = markdown.markdown(
                    article["_source"]["article"], extensions=['markdown.extensions.extra'])
                html = unescape(html)

                def _repl(mth):
                    parts = urlparse(mth.group(1))
                    params = dict(p.split("=", 1) for p in parts.query.split("&"))
                    return urljoin(request.host_url, get_cut_file_name("", **params).strip("/"))
                html = re.sub(r'(?<=src\=")(.+?)(?=")', _repl, html)
                buffer = HTML(string=html).write_pdf(
                    stylesheets=[os.path.join(project_path, "static/css/github.css")])
                ext = "pdf"
            zf.writestr("%s.%s" % (article["_source"]["title"], ext),
                        buffer or article["_source"]["article"].encode("utf-8"))
        for article in articles:
            body = "\n".join([
                article["_source"]["article"],
                "[comment]: <tags> (%s)" % ",".join(article["_source"]["tags"]),
                "[comment]: <description> (%s)" % article["_source"]["description"],
                "[comment]: <title> (%s)" % article["_source"]["title"],
                "[comment]: <author> (%s)" % article["_source"]["author"],
            ])
            zf.writestr(
                "%s.md" % article["_source"]["title"], body.encode("utf-8"))
    finally:
        zf.close()
        zip_file.seek(0)
        body = zip_file.read()
        zip_file.close()
    response = make_response(body)
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = \
        'attachment; filename="%s.zip"' % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return response


@app.route("/modify", methods=["post"])
def modify():
    if not session.get("login"):
        return json.dumps({"result": 0})
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = False
    article = h2t.handle(request.form.get("article"))
    img_url = request.form.get("img_url")
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
            "article": "[comment]: <image> (![](%s))\n%s" % (img_url, article),
            "author": author,
            "feature": feature,
            "updated_at": datetime.datetime.now(tz),
        }
    }
    db.update(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id, body=body)
    return json.dumps({"result": 1})


@app.route("/edit")
def edit():
    id = request.args.get("id")
    doc = db.get(app.config.get("INDEX"), doc_type=app.config.get("DOC_TYPE"), id=id)
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
    db.delete(
        app.config.get("INDEX"),
        id=request.args.get("id"),
        doc_type=app.config.get("DOC_TYPE"))
    return redirect(url_for("index"))


@app.route("/article")
def article():
    article = db.get(
        app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=request.args.get("id"))
    format_article_body = markdown.markdown(
        article["_source"]["article"], extensions=['markdown.extensions.extra'])
    _, articles = format_articles([article])
    article = articles[0]
    article["article"] = format_article_body
    return json.dumps(article)


@app.route("/me")
def me():
    if request.args.get("code") != next(code_generator):
        return json.dumps({"error": True})
    id = "me"
    article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id)
    if article:
        article = article["_source"]
    else:
        created_at = datetime.datetime.now(tz)
        article = {
            "id": id,
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
    article["first_img"] = get_image(article["article"])
    article["article"] = markdown.markdown(article["article"],
                                        extensions=['markdown.extensions.extra'])
    return json.dumps(article)


@app.route("/contact")
def contact():
    id = "contact"
    article = db.get(app.config.get("INDEX"), app.config.get("DOC_TYPE"), id=id)
    if article:
        article = article["_source"]
    else:
        created_at = datetime.datetime.now(tz)
        article = {
            "id": id,
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
    article["first_img"] = get_image(article["article"])
    article["article"] = markdown.markdown(article["article"],
                                        extensions=['markdown.extensions.extra'])
    return json.dumps(article)


@app.route("/show")
def show():
    count, articles, feature_articles = db.search(
        app.config.get("INDEX"), app.config.get("DOC_TYPE"),
        request.args.get("searchField"), request.args.get("from", 0),
        request.args.get("size", 20), request.args.get("fulltext") == "true")
    # es获取全部tag的方法未实现，只能返回总数
    if app.config.get("DB", "es").lower() != "es":
        tags = count
        count = len(count)
    else:
        tags = None
    tags, articles = format_articles(articles, tags=tags)
    _, feature_articles = format_articles(feature_articles)
    return json.dumps({
        "count": count,
        "articles": articles,
        "feature_articles": feature_articles,
        "tags": [i for i in sorted(tags.items(), key=lambda x: x[1], reverse=True)]})


@app.route("/cut")
def cut():
    url = request.args.get("url")
    top = request.args.get("top", 0)
    left = request.args.get("left", 0)
    width = request.args.get("width", 0)
    height = request.args.get("height", 0)

    save_name = get_cut_file_name(project_path, url, top, left, width, height)
    try:
        cuter.cut(url, save_name, top, left, width, height)
    except Exception:
        import traceback
        traceback.print_exc()
    return redirect(save_name.replace(project_path, ""))
