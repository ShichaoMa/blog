import os
import logging

from star_builder import SoloManager

app_name = "blog"


def run():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)d %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S'
    )
    SoloManager(
        app_name, current_dir=os.path.dirname(os.path.abspath(__file__))).start()


if __name__ == "__main__":
    run()
