import pathlib

from mypy_upgrade.__main__ import get_module_paths


def test_should_return_path_of_testfile():
    path = get_module_paths([__name__])[0]
    assert path == pathlib.Path(__file__).resolve()


def test_should_return_path_of_testdir():
    path = get_module_paths(["mypy_upgrade"])[0]
    assert path == pathlib.Path(__file__, "../../src/mypy_upgrade").resolve()
