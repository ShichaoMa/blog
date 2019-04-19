import pytz
import typing
import logging
import datetime

from itertools import repeat
from collections import MutableSequence, MutableSet, defaultdict

from apistellar.types import PersistentType
from apistellar.persistence import conn_ignore
from apistellar import validators, settings

from blog.blog.lib import SqliteDriverMixin
from blog.blog.utils import code_generator

from .format import Tags, Timestamp


logger = logging.getLogger("article")


class Article(PersistentType, SqliteDriverMixin):
    """
    文章模型
    :param title: 标题
    :ex `我的主页`
    :param id: 每篇文章的唯一id，日期字符串的形式表示
    :param tags: 关键字
    :ex tags:
    `["python", "apistellar"]`
    :param description: 描述信息
    :param author: 作者信息
    :param feature: 是否为精品
    :ex feature: True/False
    :param updated_at: 更新时间
    :param created_at: 创建时间
    :param show: 是否在文章列表中展示
    :ex show: True/False
    :param article: 文章正文
    """
    TABLE = "articles"

    title = validators.String()
    id = validators.String(default=lambda: datetime.datetime.now(
            pytz.timezone(settings["TIME_ZONE"])).strftime("%Y%m%d%H%M%S"))
    tags = Tags()
    description = validators.String(default="")
    author = validators.String(default=settings.get("AUTHOR"))
    feature = validators.Boolean(default=False)
    created_at = Timestamp(default=lambda: datetime.datetime.now().timestamp())
    updated_at = Timestamp(default=lambda: datetime.datetime.now().timestamp())
    show = validators.Boolean(default=True)
    article = validators.String(default=str)

    @classmethod
    def right_code(cls, code, code_gen=None):
        """
        code是否正确
        :param code:
        :param code_gen:
        :return:
        """
        if code_gen is None:
            code_gen = code_generator(
                settings.get_int("CODE_EXPIRE_INTERVAL"))

        if settings.get_bool("NEED_CODE"):
            return next(code_gen) == code
        else:
            return True

    @classmethod
    async def load(cls, **kwargs):
        """
        查找一篇文章
        :param kwargs:
        :return:
        """
        vals, sql = cls._build_select_sql(kwargs)
        cls.store.execute(sql, vals)
        data = cls.store.fetchone()

        if data:
            return cls(dict(zip(
                (col[0] for col in cls.store.description), data)))
        else:
            return Article()

    @classmethod
    async def load_list(cls, _from=None, size=None, sub=None,
                        vals=None, projection=None, **kwargs):
        """
        查询文章列表
        :param _from:
        :param size:
        :param sub:
        :param vals:
        :param kwargs:
        :param projection:
        :return:
        """
        vals, sql = cls._build_select_sql(
            kwargs, _from, size, projection, [("updated_at", "desc")], sub, vals)
        cls.store.execute(sql, vals)
        data_list = cls.store.fetchall()
        desc = [col[0] for col in cls.store.description]
        return [Article(dict(zip(desc, data))) for data in data_list]

    @classmethod
    async def get_total_tags(cls):
        """
        获取全部文章数量及每个tag的数量
        :return:
        """
        count = 0
        group_tags = defaultdict(int)
        for article in await cls.load_list(projection=["tags"], show=True):
            for tag in article.tags.split(","):
                group_tags[tag] += 1
            count += 1
        return count, group_tags

    async def save(self):
        """
        保存文章
        :return:
        """
        self.format(allow_coerce=True)
        self.store.execute(
            f"INSERT INTO {self.TABLE} VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (self.id,
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
        """
        删除文章
        :return:
        """
        self.store.execute(
            f"DELETE FROM {self.TABLE} WHERE show=1 and id=?;", (self.id, ))

    async def update(self):
        """
        更新文章
        :return:
        """
        self.store.execute(*self._build_update_sql(self))

    @classmethod
    def _build_update_sql(cls, article):
        sql = f"UPDATE {cls.TABLE} SET "
        args = list()
        for name in article:
            # 在调用update之前使用了format,目前format会创建字符串时间
            # 无法使用，在这里进行一次排除
            if name not in ("id", "updated_at", "created_at", "show"):
                article.reformat(name, allow_coerce=True)
                sql += f"{name}=?, "
                args.append(article[name])

        sql += f"updated_at=? WHERE id=?;"
        args.append(int(datetime.datetime.now().timestamp()))
        args.append(article.id)
        return sql, args

    @classmethod
    @conn_ignore
    async def search(cls, search_field, _from, size, fulltext=False, **kwargs):
        """
        搜索文章
        :param search_field:
        :param _from:
        :param size:
        :param fulltext:
        :param kwargs:
        :return:
        """
        sub, vals = cls._fuzzy_search_sub_sql(search_field, fulltext)
        return await cls.load_list(
            _from=_from, size=size, sub=sub, vals=vals, **kwargs)

    @staticmethod
    def _fuzzy_search_sub_sql(search_field, fulltext):
        """
        获取模糊搜索where子句
        :param search_field: 搜索词
        :param fulltext: 是否是全文搜索，如果是的话，则从article和tags中搜索
        :return:
        """
        sub, vals = None, None
        if search_field:
            vals = list()
            if fulltext:
                sub = f" AND (article LIKE ? OR tags LIKE ?)"
                vals.append(f"%{search_field}%")
            else:
                sub = " AND tags LIKE ?"
            vals.append(f"%{search_field}%")
        return sub, vals

    @classmethod
    def _build_select_sql(
            cls,
            kwargs: dict=None,
            _from: int=None,
            size: int=None,
            projection: list=None,
            order_fields: typing.List[typing.Tuple[str, str]]=None,
            sub: str=None,
            vals: list=None):
        """
        创建查询sql
        :param kwargs: 查询参数
        :param _from: 从哪一个开始查
        :param size: 查几个
        :param projection: 需要查哪
        :param order_fields: 按哪个字段排序
        :ex order_fields: `[("id", "desc)..]`
        :param sub: where子句
        :param vals: 占位符实参
        :return:
        """
        if vals is None:
            vals = list()

        if sub is None:
            sub = ""

        for k, v in (kwargs or dict()).items():
            if isinstance(v, (MutableSequence, MutableSet, tuple)):
                sub += f' AND {k} IN ({", ".join(repeat("?", len(v)))})'
                vals.extend(v)
            else:
                sub += " AND {}=?".format(k)
                vals.append(v)

        if order_fields:
            sub += f" order by {''.join(f + ' ' + o for f, o in order_fields)}"

        if size is not None:
            assert _from is not None, "Both of size and _from cannot be None!"
            sub += f" limit {size} offset {_from}"

        if projection:
            fields = ", ".join(projection)
        else:
            fields = "*"
        return vals, f"SELECT {fields} FROM {cls.TABLE} WHERE 1=1{sub};"
