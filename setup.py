import os
import re
import string

from contextlib import contextmanager
from setuptools import find_packages, setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    mth = re.search("__version__\s?=\s?['\"]([^'\"]+)['\"]", init_py)
    if mth:
        return mth.group(1)
    else:
        raise RuntimeError("Cannot find version!")
        
        
def install_requires():
    """
    Return requires in requirements.txt
    :return:
    """
    try:
        with open("requirements.txt") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except OSError:
        return []


@contextmanager
def cfg_manage(cfg_tpl_filename):
    if os.path.exists(cfg_tpl_filename):
        cfg_file_tpl = open(cfg_tpl_filename)
        buffer = cfg_file_tpl.read()
        try:
            with open(cfg_tpl_filename.rstrip(".tpl"), "w") as cfg_file:
                cfg_file.write(string.Template(buffer).substitute(
                    pwd=os.path.abspath(os.path.dirname(__file__))))
            yield
        finally:
            cfg_file_tpl.close()
    else:
        yield


with cfg_manage(__file__.replace(".py", ".cfg.tpl")):
    setup(
        name="blog",
        version=get_version("blog"),
        packages=find_packages(exclude=("tests",)),
        include_package_data=True,
        install_requires=install_requires(),
        author="",
        author_email="",
        description="""package description here""",
        keywords="",
        setup_requires=["pytest-runner"],
        tests_require=["pytest-apistellar", "pytest-asyncio", "pytest-cov"]
    )
