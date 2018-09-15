import os
import sqlite3
import typing

from apistellar import Component
from toolkit.settings import FrozenSettings

from .utils import code_generator, project_path
from .lib import Sqlite
from .lib.html_cut import Cuter
Code = typing.NewType("Code", str)


class SqliteComponent(Component):

    def __init__(self):
        os.makedirs(os.path.join(project_path, "db"), exist_ok=True)
        self.table_initialize = open(
            os.path.join(project_path, "blog.sql")).read()
        self.conn = sqlite3.connect(os.path.join(project_path, "db/blog"))
        self.cur = self.conn.cursor()
        try:
            self.cur.execute(self.table_initialize)
        except sqlite3.OperationalError as e:
            pass

    def resolve(self) -> Sqlite:
        return Sqlite(self.cur, self.conn)


class CodeComponent(Component):

    def __init__(self):
        self.code_generator = None

    def resolve(self, settings: FrozenSettings) -> Code:
        if self.code_generator is None:
            self.code_generator = code_generator(settings.CODE_EXPIRE_INTERVAL)
        return Code(next(self.code_generator))


class CuterComponent(Component):
    def __init__(self):
        self.cutter = None

    def resolve(self, settings: FrozenSettings) -> Cuter:
        if self.cutter is None:
            self.cutter = Cuter(
                settings.PHANTOMJS_PATH, os.path.join(project_path, "cut_html.js"))
        return self.cutter
