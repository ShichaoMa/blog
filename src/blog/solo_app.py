import os
import logging

from apistellar import SoloManager

app_name = "blog"


def run():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
    SoloManager(
        app_name, current_dir=os.path.dirname(os.path.abspath(__file__))).start()


if __name__ == "__main__":
    run()
