import os
import time

from collections import UserDict


class Cuter(object):

    def __init__(self, phantomjs_path, js_path):
        self.phantomjs_path = phantomjs_path
        self.js_path = js_path
        self.loader = LazyLoader(self._cut)

    def cut(self, url, save_name, top=0, left=0, width=1024, height=768):
        return self.loader[Picture(url, save_name, top, left, width, height)]

    def _cut(self, url, save_name, top, left, width, height):
        try:
            os.system(("%s "*8) % (self.phantomjs_path, self.js_path, url, save_name, top, left, width, height))
            return True
        except Exception as e:
            print(e)
            return False


class Picture(object):

    def __init__(self, url, save_name, top, left, width, height, refresh=1000):
        self.url = url
        self.save_name = save_name
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.ts = time.time()
        self.refresh = refresh

    def __hash__(self):
        return hash(self.url) + hash(self.save_name) + \
               hash(self.top) + hash(self.left) + hash(self.width) + hash(self.height)

    def __eq__(self, other):
        return self.url == other.url and \
               self.save_name == other.save_name and \
               self.top == other.top and \
               self.left == other.left and \
               self.width == self.url and \
               self.height == self.height

    def __iter__(self):
        return iter([self.url, self.save_name, self.top, self.left, self.width, self.height])


class LazyLoader(UserDict):

    def __init__(self, callback):
        super(LazyLoader, self).__init__()
        self.callback = callback

    def __getitem__(self, key):
        pic = self.data.get(key, key)
        if key not in self.data or time.time() - pic.refesh > pic.ts:
            if self.callback(*key):
                self.data[key] = key
                return key
        else:
            return pic
