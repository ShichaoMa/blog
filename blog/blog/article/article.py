import logging
import datetime

from itertools import repeat

from apistellar.types import PersistentType
from apistellar.persistence import conn_ignore
from apistellar import validators, ModelFactory, SettingsMixin

from ..lib import SqliteDriverMixin
from .format import Tags, Boolean, Timestamp
from ..utils import decode, get_id, get_cut_file_name, code_generator


settings_wrapper = SettingsMixin()


logger = logging.getLogger(__file__)


class Article(PersistentType, SqliteDriverMixin, SettingsMixin):
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
    id = validators.String(default=get_id)
    tags = Tags()
    description = validators.String(default="")
    author = validators.String(default=settings_wrapper.settings["AUTHOR"])
    feature = Boolean(default=False)
    created_at = Timestamp(default=datetime.datetime.now().timestamp)
    updated_at = Timestamp(default=datetime.datetime.now().timestamp)
    show = Boolean(default=True)
    article = validators.String(default=str)

    @classmethod
    def right_code(cls, code, code_gen=None):
        """
        code是否正确
        :param code:
        :return:
        """
        if code_gen is None:
            code_gen = code_generator(
                cls.settings.get_int("CODE_EXPIRE_INTERVAL"))

        if cls.settings.get_bool("NEED_CODE"):
            return next(code_gen) == code
        else:
            return True

    async def load(self, **kwargs):
        """
        查找一篇文章
        :param kwargs:
        :return:
        """
        if not kwargs:
            kwargs["id"] = self.id
        sub, args = self.build_sub_sql(kwargs)
        self.store.execute(f"SELECT * FROM {self.TABLE} WHERE 1=1 {sub}", args)
        data = self.store.fetchone()

        if data:
            new = Article(dict(zip(
                (col[0] for col in self.store.description), data)))
        else:
            new = Article()
        super(Article, self).update(**new)
        return new

    @classmethod
    async def load_list(cls, ids, projection=None, _from=None,
                        size=None, sub="", args=None, **kwargs):
        """
        查询文章列表
        :param ids:
        :param projection:
        :param _from:
        :param size:
        :param sub:
        :param args:
        :param kwargs:
        :return:
        """
        sub, args = cls.build_sub_sql(kwargs, sub, args)
        if ids:
            sub += 'and id in ({})'.format(", ".join(repeat("?", len(ids))))
            args.extend(ids)
        sub += " order by updated_at desc"
        if size:
            sub += f" limit {size} offset {_from}"
        sub += ";"
        if projection:
            fields = ", ".join(projection)
        else:
            fields = "*"
        sql = f"SELECT {fields} FROM {cls.TABLE} WHERE 1=1 {sub}"
        cls.store.execute(sql, args)
        data_list = cls.store.fetchall()
        return [Article(dict(zip(
            (col[0] for col in cls.store.description), data)))
            for data in data_list]

    @staticmethod
    def build_sub_sql(kwargs, sub="", args=None):
        """
        创建查询子串
        :param kwargs: 需要连接的key val mapping
        :param sub: 已存在的子串
        :param args: 已存在的args
        :return:
        """
        if args is None:
            args = list()

        for k, v in kwargs.items():
            sub += " AND {}=?".format(k)
            args.append(v)
        return sub, args

    async def save(self):
        """
        保存文章
        :return:
        """
        self.format()
        self.store.execute(
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
        sql = f"UPDATE {self.TABLE} SET "
        args = []
        self.format()

        for name, val in self.items():
            # 在调用update之前使用了format,目前format会创建字符串时间
            # 无法使用，在这里进行一次排除
            if name not in ("id", "updated_at", "created_at", "show"):
                sql += f"{name}=?, "
                args.append(val)

        sql += f"updated_at=? WHERE id=?;"
        args.append(int(datetime.datetime.now().timestamp()))
        args.append(self.id)
        logger.debug(f"Execute sql: {sql}, args: {args}")
        self.store.execute(sql, args)

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
