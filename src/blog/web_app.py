import os
import logging

from uvicorn import run
from apistellar import Application
from whitenoise import WhiteNoise

# 静态文件每次请求重新查找
WhiteNoise.autorefresh = True

app_name = "blog"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

app = Application(
    app_name, debug=False,
    current_dir=os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    run(app)
