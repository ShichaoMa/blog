# -*- coding:utf-8 -*-
import os
import pytz
import json
import sqlite3
import elasticsearch

from abc import ABC, abstractmethod

from .utils import conn_wrapper, format_data, project_path


class Driver(ABC):

    @abstractmethod
    def index(self, index, doc_type, id, body):
        pass

    @abstractmethod
    def get(self, index, doc_type, **kwargs):
        pass

    @abstractmethod
    def update(self, index, doc_type, id, body):
        pass

    @abstractmethod
    def delete(self, index, doc_type, id):
        pass

    @abstractmethod
    def search(self, index, doc_type, search_field, _from, size, fulltext=False):
        pass

    @abstractmethod
    def gen_article(self, index, doc_type, id):
        pass



class DataBase(Driver):

    def __init__(self, config):
        self.config = config
        if self.config.get("DB", "es").lower() == "es":
            self.driver = ElasticSearchDriver(config)
        else:
            self.driver = Sqlite3Diver(config)

    def index(self, index, doc_type, id, body):
        return self.driver.index(index, doc_type, id, body)

    def get(self, index, doc_type, **kwargs):
        return self.driver.get(index, doc_type, **kwargs)

    def update(self, index, doc_type, id, body):
        return self.driver.update(index, doc_type, id, body)

    def delete(self, index, doc_type, id):
        return self.driver.delete(index, doc_type, id)

    def search(self, index, doc_type, search_field, _from, size, fulltext=False):
        return self.driver.search(index, doc_type, search_field, _from, size, fulltext)

    def gen_article(self, index, doc_type, id):
        return self.driver.gen_article(index, doc_type, id)


class Sqlite3Diver(Driver):
    """
    使用sqlite3做存储
    """

    def __init__(self, config):
        self.config = config
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
    def index(self, index, doc_type, id, body):
        self.cur.execute("INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);".format(doc_type), (
                id, body["description"], ",".join(body["tags"]), body["article"], body["author"], body["title"],
                1 if body["feature"] else 0, int(body["created_at"].timestamp()), int(body["updated_at"].timestamp()),
                body["show"]))

    @conn_wrapper
    def get(self, index, doc_type, **kwargs):
        sub = ""
        args = list()
        for k, v in kwargs.items():
            sub += "and {}=?".format(k)
            args.append(v)
        self.cur.execute("SELECT * FROM {} WHERE 1=1 {}".format(doc_type, sub), tuple(args))
        data = self.cur.fetchone()
        if data:
            return format_data(data, tz=pytz.timezone(self.config.get("TIME_ZONE")))
        return ""

    @conn_wrapper
    def update(self, index, doc_type, id, body):
        self.cur.execute("UPDATE {} SET description=?, tags=?, article=?, author=?,"
                             " title=?, feature=?, updated_at=? WHERE id=?;".format(doc_type), (
                                 body["doc"]["description"], ",".join(body["doc"]["tags"]), body["doc"]["article"],
                                 body["doc"]["author"], body["doc"]["title"], 1 if body["doc"]["feature"] else 0,
                                 int(body["doc"]["updated_at"].timestamp()), id
                             ))
        self.conn.commit()

    @conn_wrapper
    def delete(self, index, doc_type, id):
        self.cur.execute("DELETE FROM %s WHERE show=1 and id='%s';" % (doc_type, id))
        self.conn.commit()

    @conn_wrapper
    def search(self, index, doc_type, search_field, _from, size, fulltext=False):
        if fulltext:
            sub = "AND (article LIKE '%%%s%%' OR tags LIKE '%%%s%%')" % (
                search_field, search_field) if search_field else ""
        else:
            sub = "AND tags LIKE '%%%s%%'" % search_field if search_field else ""
        self.cur.execute("SELECT * FROM %s WHERE show=1 %s ORDER BY updated_at desc limit %s offset %s;" % (
            doc_type, sub, size, _from))
        rs = self.cur.fetchall()
        self.cur.execute("SELECT tags FROM %s WHERE show=1" % doc_type)
        tags = self.cur.fetchall()
        self.cur.execute(
            "SELECT * FROM %s WHERE show=1 AND feature=1 %s ORDER BY updated_at desc limit %s offset %s;" % (
                doc_type, sub, size, _from))
        return tags, [format_data(data, tz=pytz.timezone(self.config.get("TIME_ZONE"))) for data in rs], \
               [format_data(data, tz=pytz.timezone(self.config.get("TIME_ZONE"))) for data in self.cur.fetchall()]

    @conn_wrapper
    def gen_article(self, index, doc_type, id):
        if not id:
            return ""
        self.cur.execute("SELECT article FROM %s WHERE id='%s';" % (doc_type, id))
        data = self.cur.fetchone()
        if data:
            return data[0]
        return ""


class ElasticSearchDriver(Driver):

    def __init__(self, config):
        self.config = config
        self.table_initialize = open(os.path.join(project_path, "blog.json")).read()
        self.conn = elasticsearch.Elasticsearch(config.get("ES_HOST"), http_auth=(config.get("ES_USERNAME"), config.get("ES_PASSWORD")))
        self.conn.indices.create(config.get("INDEX"), body=json.loads(self.table_initialize), ignore=400)

    def index(self, index, doc_type, id, body):
        return self.conn.index(index, doc_type, id=id, body=body)

    def get(self, index, doc_type, id):
        data = self.conn.get(index, id=id, doc_type=doc_type, ignore=404)
        if data["found"]:
            return data
        return ""

    def update(self, index, doc_type, id, body):
        return self.conn.update(index, doc_type, id=id, body=body)

    def delete(self, index, doc_type, id):
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

    def search(self, index, doc_type, search_field, _from, size, fulltext=False):
        condition = {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "_all" if fulltext else "tags": search_field
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
                "bool": {
                    "must": [
                        {
                            "term": {
                                "show": 1
                            }
                        }
                    ]
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

    def gen_article(self, index, doc_type, id):
        if not id:
            return ""
        data = self.conn.get(index, id=id, doc_type=doc_type)
        if data["found"]:
            return data["_source"]["article"]
        return ""
