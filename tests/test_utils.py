import time
import pytest

from blog.blog.utils import code_generator, get_stored_code, gen_code

from factories import get_code


def test_gen_code(join_root_dir):
    code, last_time = gen_code(0, 3600, join_root_dir("test_data/"))
    assert len(code) == 6
    assert last_time - int(time.time()) < 1


def test_gen_code_not_expired(join_root_dir):
    rs = gen_code(time.time(), 3600, join_root_dir("test_data/"))
    assert rs is None


def test_get_stored_code(join_root_dir):
    code, last_time = get_stored_code(join_root_dir("test_data/"))
    assert len(code) == 6
    assert isinstance(last_time, int)


@pytest.mark.prop("blog.blog.utils.get_stored_code", ret_val=("ABCDEF", 111))
@pytest.mark.prop("blog.blog.utils.gen_code")
def test_code_generator_stored_not_expired():
    gen = code_generator(10)
    assert next(gen) == "ABCDEF"


# 通过打开一个假文件来触发一次OSError
@pytest.mark.prop("blog.blog.utils.get_stored_code",
                  ret_factory=lambda *args, **kwargs: open("/tmp/abc/abc/abc"))
def test_code_generator_not_stored_expired():
    gen = code_generator(10)
    assert next(gen) == get_code()
