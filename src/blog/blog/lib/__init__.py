import os
import sqlite3
import logging

from pyaop import AOP, Proxy
from apistellar.persistence import DriverMixin, proxy, contextmanager
from apistellar.helper import cache_classproperty

from ..utils import project_path


logger = logging.getLogger("sql")


class SqliteProxy(Proxy):
    proxy_methods = ["execute"]


def execute_before(self, *args, **kwargs):
    logger.debug(f"Execute sql: `{args[0]}`  args: `{args[1]}`")


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
            cur = conn.cursor()
            store = SqliteProxy(
                cur, before=[AOP.Hook(execute_before, ["execute"])])
            try:
                yield proxy(self_or_cls, prop_name="store", prop=store)
            finally:
                conn.commit()

