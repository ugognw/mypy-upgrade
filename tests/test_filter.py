from __future__ import annotations

import pathlib
import sys
from importlib import util

import pytest

from mypy_upgrade.filter import filter_mypy_errors, get_module_paths
from mypy_upgrade.parsing import MypyError

MODULES = [
    "ast",
    "collections.abc",
]

MODULE_PATHS = [
    "ast.py",
    "collections/abc.py",
]


class TestGetModulePaths:
    if sys.version_info < (3, 10):
        MODULES_AND_MODULE_PATHS = zip(MODULES, MODULE_PATHS)
    else:
        MODULES_AND_MODULE_PATHS = zip(MODULES, MODULE_PATHS, strict=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("module", "module_path"), MODULES_AND_MODULE_PATHS
    )
    def test_should_return_path_of_modules(
        module: str, module_path: str
    ) -> None:
        spec = util.find_spec(module)
        assert spec is not None
        assert spec.origin is not None
        assert spec.origin.endswith(module_path)

    @staticmethod
    def test_should_return_path_of_testfile() -> None:
        path = get_module_paths(["mypy_upgrade.cli"])[0]
        assert path == pathlib.Path("src/mypy_upgrade/cli.py").resolve()

    @staticmethod
    def test_should_return_path_of_testdir() -> None:
        path = get_module_paths(["mypy_upgrade"])[0]
        assert (
            path == pathlib.Path(__file__, "../../src/mypy_upgrade").resolve()
        )

    @staticmethod
    def test_should_return_none_for_nonexistent_module() -> None:
        path = get_module_paths(["fake_module"])[0]
        assert path is None

    @staticmethod
    def test_should_raise_error_for_built_in_module() -> None:
        with pytest.raises(NotImplementedError) as exc_info:
            _ = get_module_paths(["sys"])
        message = "Uncountered an unsupported module type."
        assert exc_info.value.args[0] == message


@pytest.fixture(
    name="packages_to_include",
    params=(
        [],
        ["os", "xml.sax"],
    ),
)
def fixture_packages_to_include(request: pytest.FixtureRequest) -> list[str]:
    packages_to_include: list[str] = request.param
    return packages_to_include


@pytest.fixture(
    name="modules_to_include",
    params=(
        [],
        ["pathlib", "xml.sax.handler"],
    ),
)
def fixture_modules_to_include(request: pytest.FixtureRequest) -> list[str]:
    modules_to_include: list[str] = request.param
    return modules_to_include


@pytest.fixture(
    name="files_to_include",
    params=(
        [],
        ["pathlib.py", "xml/sax/handler.py"],
    ),
)
def fixture_files_to_include(request: pytest.FixtureRequest) -> list[str]:
    files_to_include: list[str] = request.param
    return files_to_include


class TestFilterMypyErrors:
    @staticmethod
    @pytest.mark.slow
    def test_should_only_include_selected_packages(
        parsed_errors: list[MypyError], packages_to_include: list[str]
    ) -> None:
        filtered_errors = filter_mypy_errors(
            parsed_errors, packages_to_include, [], []
        )
        if packages_to_include:
            packages_supposed_to_be_included = []
            for error in filtered_errors:
                packages_supposed_to_be_included.append(
                    any(p in error.filename for p in packages_to_include)
                )
            assert all(packages_supposed_to_be_included)
        else:
            assert filtered_errors == parsed_errors

    @staticmethod
    @pytest.mark.slow
    def test_should_only_include_selected_modules(
        parsed_errors: list[MypyError], modules_to_include: list[str]
    ) -> None:
        filtered_errors = filter_mypy_errors(
            parsed_errors, modules_to_include, [], []
        )
        if modules_to_include:
            modules_supposed_to_be_included = []
            for error in filtered_errors:
                modules_supposed_to_be_included.append(
                    any(m in error.filename for m in modules_to_include)
                )
            assert all(modules_supposed_to_be_included)
        else:
            assert filtered_errors == parsed_errors

    @staticmethod
    @pytest.mark.slow
    def test_should_only_include_selected_files(
        parsed_errors: list[MypyError], files_to_include: list[str]
    ) -> None:
        filtered_errors = filter_mypy_errors(
            parsed_errors, [], [], files_to_include
        )
        if files_to_include:
            assert all(
                error.filename in files_to_include for error in filtered_errors
            )
        else:
            assert filtered_errors == parsed_errors

    @staticmethod
    @pytest.mark.slow
    def test_should_only_include_selected_combinations(
        parsed_errors: list[MypyError],
        packages_to_include: list[str],
        modules_to_include: list[str],
        files_to_include: list[str],
    ) -> None:
        filtered_errors = filter_mypy_errors(
            parsed_errors,
            packages_to_include,
            modules_to_include,
            files_to_include,
        )

        to_include = (
            packages_to_include + modules_to_include + files_to_include
        )
        if to_include:
            supposed_to_be_included = []
            for error in filtered_errors:
                supposed_to_be_included.append(
                    any(path in error.filename for path in to_include)
                )
            assert all(supposed_to_be_included)
        else:
            assert filtered_errors == parsed_errors
