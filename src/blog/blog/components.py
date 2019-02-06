import os
import sqlite3
import typing

from toolkit.settings import FrozenSettings
from apistellar import Component, settings

from .lib.html_cut import Cuter
from .utils import code_generator
Code = typing.NewType("Code", str)


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
                settings.PHANTOMJS_PATH, os.path.join(
                    settings["PROJECT_PATH"], "cut_html.js"))
        return self.cutter
