import os
import logging

from uvicorn import run
from apistellar import Application
from whitenoise import WhiteNoise

# 静态文件每次请求重新查找
WhiteNoise.autorefresh = True

app_name = "blog"
logging.basicConfig(level=logging.DEBUG)
app = Application(app_name, debug=False,
                  static_dir="static", template_dir="templates",
                  current_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if __name__ == "__main__":
    run(app)
