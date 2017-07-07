# -*- coding:utf-8 -*-
import os
import json
import codecs
import markdown
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request


app = Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templetes")

es = Elasticsearch("localhost:9200")


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/artile")
def artile():
    input_file = codecs.open(os.path.join("articles", "%s.md"%request.args.get("id")), mode="r", encoding="utf-8")
    text = input_file.read()
    return json.dumps({"body": markdown.markdown(text, extensions=['markdown.extensions.extra'])})


@app.route("/me")
def me():
    return json.dumps({"author":"马式超", "body": "<p>这是我的一段简单介绍</p>", "title": "我的自我介绍", "created_at": "2017-07-08T12:12:12"})


@app.route("/contact")
def contact():
    return json.dumps({"author":"马式超", "body": "<p>这是我的联系方式</p>", "title": "我的联系方式", "created_at": "2017-07-08T12:12:12"})


@app.route("/index/show")
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
            tags[tag] = tags.setdefault(tag, 0) + 1
        format_articles.append(article)
    return json.dumps({"articles": format_articles, "tags": [i[0] for i in sorted(tags.items(), key=lambda x: x[1], reverse=True)]})

if __name__ == "__main__":
    app.run(debug=True)