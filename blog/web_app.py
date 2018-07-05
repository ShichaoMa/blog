import os
import sys
import logging

from uvicorn import run
from star_builder import Application
from whitenoise import WhiteNoise
# 静态文件每次请求重新查找
WhiteNoise.autorefresh = True

app_name = "blog"

# 以下几行代码的目的是为了在将整个项目打成一包安装，并做为模块被uvicorn使用时
# 保证可以自动加载该项目下所有模块。
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
sys.path.insert(0, current_dir)
sys.modules.pop(app_name, None)

logging.basicConfig(level=logging.DEBUG)


app = Application(static_dir="static", template_dir="templates")


if __name__ == "__main__":
    run(app)
