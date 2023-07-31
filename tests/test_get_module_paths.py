import pathlib

from mypy_upgrade.cli import get_module_paths


def test_should_return_path_of_testfile():
    path = get_module_paths(["mypy_upgrade.cli"])[0]
    assert path == pathlib.Path("src/mypy_upgrade/cli.py").resolve()


def test_should_return_path_of_testdir():
    path = get_module_paths(["mypy_upgrade"])[0]
    assert path == pathlib.Path(__file__, "../../src/mypy_upgrade").resolve()
