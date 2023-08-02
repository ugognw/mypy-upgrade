import pathlib
from importlib import util

import pytest

from mypy_upgrade.filter import get_module_paths

MODULES = [
    "ase.atoms",
    "ase.calculators.vasp.vasp",
    "ast",
    "collections.abc",
    "pytest",
    "typing",
]

MODULE_PATHS = [
    "ase/atoms.py",
    "ase/calculators/vasp/vasp.py",
    "ast.py",
    "collections/abc.py",
    "pytest/__init__.py",
    "typing.py",
]


@pytest.mark.parametrize(
    ("module", "module_path"), zip(MODULES, MODULE_PATHS, strict=True)
)
def test_should_return_path_of_modules(module: str, module_path: str):
    spec = util.find_spec(module)
    assert spec is not None
    assert spec.origin is not None
    assert spec.origin.endswith(module_path)


def test_should_return_path_of_testfile():
    path = get_module_paths(["mypy_upgrade.cli"])[0]
    assert path == pathlib.Path("src/mypy_upgrade/cli.py").resolve()


def test_should_return_path_of_testdir():
    path = get_module_paths(["mypy_upgrade"])[0]
    assert path == pathlib.Path(__file__, "../../src/mypy_upgrade").resolve()
