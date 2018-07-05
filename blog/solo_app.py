import os
import sys
import logging

from star_builder import SoloManager


def run():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)d %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S'
    )
    # 以下几行代码的目的是为了在将整个项目打成一包安装时
    # 保证可以自动加载该项目下所有模块。
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)
    SoloManager().start()


if __name__ == "__main__":
    run()
