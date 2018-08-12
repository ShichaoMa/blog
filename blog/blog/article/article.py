import numbers
import typing
import datetime

from itertools import repeat
from collections import Sequence
from toolkit.settings import FrozenSettings
from apistar.http import QueryParam, RequestData

from star_builder.types import Type
from star_builder import validators, ModelFactory, inject
from star_builder.types.formats import BaseFormat, DATETIME_REGEX, ValidationError
from ..utils import decode, get_id, default_tz
from ..components import Sqlite


class TsFormat(BaseFormat):

    type = numbers.Number
    default_tz = default_tz

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        """
        赋值和format会调用valiate，转普通类型转换成self.type类型
        :param value:
        :return:
        """
        if isinstance(value, (str, bytes)):
            match = DATETIME_REGEX.match(value)
            if match:
                kwargs = {k: int(v) for k, v in
                          match.groupdict().items() if v is not None}
                return datetime.datetime(
                    **kwargs, tzinfo=self.default_tz).timestamp()
        raise ValidationError('Must be a valid timestamp.')

    def to_string(self, value):
        """
        所有最终会调用__getitem__的方法，会调用这个方法来反序列化，__getattr__则不会。
        :param value:
        :return:
        """
        try:
            return datetime.datetime.fromtimestamp(
                value, self.default_tz).strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            return str(value)


class TagsFormat(BaseFormat):

    type = list

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        if isinstance(value, str):
            return value.split(",")
        if isinstance(value, bytes):
            return value.decode().split(",")
        if isinstance(value, Sequence):
            return list(value)
        raise ValidationError('Must be a valid tags.')

    def to_string(self, value):
        if isinstance(value, str):
            value = value.split(",")
        return ",".join(value)


class Timestamp(validators.String):

    def __init__(self, **kwargs):
        super().__init__(format='ts', **kwargs)


class Boolean(validators.Validator):
    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.has_default():
            return self.get_default()
        elif value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')

        elif not isinstance(value, bool):
            return bool(value)

        return value


class Tags(validators.String):
    def __init__(self, **kwargs):
        super().__init__(format='tags', **kwargs)


validators.FORMATS["ts"] = TsFormat()
validators.FORMATS["tags"] = TagsFormat()


class Article(Type):
    sqlite = inject << Sqlite
    TABLE = "articles"

    title = validators.String()
    id = validators.String(default=get_id)
    tags = Tags()
    description = validators.String()
    author = validators.String()
    feature = Boolean(default=False)
    created_at = Timestamp(default=datetime.datetime.now().timestamp)
    updated_at = Timestamp(default=datetime.datetime.now().timestamp)
    show = Boolean(default=True)
    article = validators.String(default=str)

    async def load(self, **kwargs):
        if not kwargs:
            kwargs["id"] = self.id
        sub, args = self.build_sub_sql(kwargs)
        with self.sqlite as cur:
            cur.execute(f"SELECT * FROM {self.TABLE} WHERE 1=1 {sub}", args)
            data = cur.fetchone()
            if data:
                new = Article(dict(zip(
                    (col[0] for col in cur.description), data)))
            else:
                new = Article()
            super(Article, self).update(**new)
            return new

    @classmethod
    async def load_list(cls, ids, projection=None,
                        _from=None, size=None, sub="",
                        args=None, **kwargs):
        sub, args = cls.build_sub_sql(kwargs, sub, args)
        if ids:
            sub += 'and id in ({})'.format(", ".join(repeat("?", len(ids))))
            args.extend(ids)
        if size:
            sub += f"limit {size} offset {_from};"
        else:
            sub += ";"
        if projection:
            fields = ", ".join(projection)
        else:
            fields = "*"

        with cls.sqlite as cur:
            cur.execute(f"SELECT {fields} FROM {cls.TABLE} WHERE 1=1 {sub}", args)
            data_list = cur.fetchall()
            return [Article(dict(zip(
                (col[0] for col in cur.description), data)))
                for data in data_list]

    @staticmethod
    def build_sub_sql(kwargs, sub="", args=None):
        if args is None:
            args = list()
        for k, v in kwargs.items():
            sub += "and {}=?".format(k)
            args.append(v)
        return sub, args

    async def save(self):
        self.format()
        with self.sqlite as cur:
            cur.execute(
                f"INSERT INTO {self.TABLE} "
                f"VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (
                self.id,
                self.description,
                # 通过下标获取，可以调用其formatter的to_string方法返回
                self["tags"],
                self.article,
                self.author,
                self.title,
                self.feature,
                self.created_at,
                self.updated_at,
                self.show))

    async def remove(self):
        with self.sqlite as cur:
            cur.execute(
                f"DELETE FROM {self.TABLE} WHERE show=1 and id=?;", (self.id, ))

    async def update(self):
        sql = f"UPDATE {self.TABLE} SET "
        args = []
        for name, value in self.items():
            if name != "id":
                sql += f"{name}=?, "
                args.append(value)

        sql += f"updated_at=? WHERE id=?;"
        args.append(int(datetime.datetime.now().timestamp()))
        args.append(self.id)

        with self.sqlite as cur:
            cur.execute(sql, args)

    @classmethod
    async def search(cls, search_field, _from, size, fulltext=False, **kwargs):
        sub, args = "", []
        if fulltext:
            if search_field:
                sub = f"AND (article LIKE ? OR tags LIKE ?)"
                args.append(f"%{search_field}%")
                args.append(f"%{search_field}%")
        else:
            if search_field:
                sub = "AND tags LIKE ?"
                args.append(f"%{search_field}%")

        return await cls.load_list(None, None, _from, size, sub, args, **kwargs)


class ArticleFactory(ModelFactory):
    model = Article

    async def product(self,
                      form: RequestData,
                      id: QueryParam,
                      settings: FrozenSettings) -> Article:
        params = {}
        if not form:
            form = {}

        file = form.get("article")
        if hasattr(file, "read"):
            params["article"] = decode(file.read())
        else:
            params["article"] = file

        params["id"] = form.get("id") or id
        params["author"] = form.get("author") or settings.AUTHOR
        params["title"] = form.get("title") or \
                          file and file.filename.replace(".md", "")
        params["feature"] = eval(form.get("feature") or "False")
        params["description"] = form.get("description") or ""
        params["tags"] = form.get("tags") or ""
        return Article(params)


class ArticleListFactory(ModelFactory):
    model = Article

    async def product(self,
                      ids: QueryParam,
                      _from: QueryParam,
                      size: QueryParam) -> typing.List[Article]:
        if ids:
            ids = ids.split(",")
        else:
            ids = []
        return await Article.load_list(ids, _from, size)
