import os
import sqlite3

from contextlib import contextmanager
from apistellar.persistence import DriverMixin
from apistellar.helper import cache_classproperty

from ..utils import project_path


class SqliteDriverMixin(DriverMixin):

    INIT_SQL_FILE = "blog.sql"
    DB_PATH = "db/blog"

    store = None  # type: sqlite3.Cursor

    @cache_classproperty
    def init_sqlite(cls):
        os.makedirs(os.path.join(
            project_path, os.path.dirname(cls.DB_PATH)), exist_ok=True)
        table_initialize = open(
            os.path.join(project_path, cls.INIT_SQL_FILE)).read()
        conn = sqlite3.connect(os.path.join(project_path, cls.DB_PATH))
        cur = conn.cursor()
        try:
            cur.execute(table_initialize)
        except sqlite3.OperationalError as e:
            pass
        return conn, cur

    @classmethod
    @contextmanager
    def get_store(cls, **kwargs):
        conn, cur = cls.init_sqlite
        try:
            yield cur
        finally:
            conn.commit()

