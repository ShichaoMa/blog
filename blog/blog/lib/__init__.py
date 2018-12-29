import os
import sqlite3

from apistellar.persistence import DriverMixin, proxy, contextmanager
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
    def get_store(cls, self_or_cls, **callargs):
        conn, cur = cls.init_sqlite
        with super(SqliteDriverMixin, cls).get_store(
                self_or_cls, **callargs) as self_or_cls:
            try:
                yield proxy(self_or_cls, prop_name="store", prop=conn.cursor())
            finally:
                conn.commit()

