import os
import time
import inspect

from functools import wraps
from threading import RLock


def free_namedtuple(func):
    """
    根据一个类及其参数创建一个类namedtuple class，但不同之处在于创建实例成功后可以自由赋值，初时化时指定的值决定其Hash和eq
    :param func:
    :return:
    """
    cls_tmpl = """
class {}(object):
    def __init__(self, {}):
        {}
    def __hash__(self):
        return {}

    def __eq__(self, other):
        return {}
        
    def __str__(self):
        return str(self.__dict__)
    
    __repr__ = __str__
"""

    args = inspect.getfullargspec(func).args
    try:
        args.remove("self")
    except ValueError:
        pass
    class_name = func.__name__.capitalize()
    init_arg = ", ".join(args)
    init_body = "".join(
        "self.{%s} = {%s}\n        " % (
            index, index) for index in range(len(args))).format(*args)
    hash_body = " + ".join("hash(self.{})".format(arg) for arg in args)
    eq_body = " and ".join("self.{0} == other.{0}".format(arg) for arg in args)
    iter_body = ", self.".join(args)
    namespace = dict(__name__='entries_%s' % class_name)
    exec(cls_tmpl.format(
        class_name, init_arg, init_body, hash_body, eq_body, iter_body), namespace)
    return namespace[class_name]


def cache_method(timeout=3600):
    """
    缓存一个方法的调用结果，持续一定时间，该方法调用正常时，希望返回真值(形式真)，或返回值为假，缓存效果会失效。
    :param timeout: 缓存时间 :s
    :return:
    """
    def cache(func):
        entry_class = free_namedtuple(func)
        data = dict()
        lock = RLock()

        @wraps(func)
        def inner(*args, **kwargs):
            with lock:
                for k in data.copy().keys():
                    if time.time() - timeout > data[k].ts:
                        del data[k]

                entry = entry_class(*args[1:], **kwargs)
                entry.ts = time.time()
                stored = data.get(entry, entry)
                if entry not in data or time.time() - timeout > stored.ts:
                    entry.result = func(*args, **kwargs)
                    if entry.result:
                        data[entry] = entry
                    return entry.result
                else:
                    return stored.result
        return inner
    return cache


class Cuter(object):

    def __init__(self, phantomjs_path, js_path):
        self.phantomjs_path = phantomjs_path
        self.js_path = js_path

    @cache_method()
    def cut(self, url, save_name, top=0, left=0, width=1024, height=768):
        os.system(("%s "*8) % (
            self.phantomjs_path,
            self.js_path,
            url,
            save_name,
            top,
            left,
            width,
            height))
        if os.path.exists(save_name):
            return True
        else:
            return False
