# -*- coding:utf-8 -*-
import os
import sqlite3
import datetime

from threading import local


local = local()
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def conn_wrapper(func):
    """
    sqlite的conn不能多个线程使用
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        self = args[0]
        index = args[1]
        if self.config.get("DB", "es").lower() != "es":
            self.conn = getattr(local, "conn", None)
            if not self.conn:
                self.conn = sqlite3.connect(os.path.join(project_path, "db", index))
                self.cur = self.conn.cursor()
        result = func(*args, **kwargs)
        if self.config.get("DB", "es").lower() != "es":
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


def format_data(data, tz):
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
