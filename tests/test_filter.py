from __future__ import annotations

import io
import pathlib
import sys
import tokenize
from collections.abc import Generator
from importlib import util

import pytest

from mypy_upgrade.filter import (
    UnsilenceableRegion,
    _find_unsilenceable_regions,
    _get_module_paths,
    _is_safe_to_silence,
    filter_by_silenceability,
    filter_by_source,
)
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
        path = _get_module_paths(modules=["mypy_upgrade.cli"])[0]
        assert path == pathlib.Path("src/mypy_upgrade/cli.py").resolve()

    @staticmethod
    def test_should_return_path_of_testdir() -> None:
        path = _get_module_paths(modules=["mypy_upgrade"])[0]
        assert (
            path == pathlib.Path(__file__, "../../src/mypy_upgrade").resolve()
        )

    @staticmethod
    def test_should_return_none_for_nonexistent_module() -> None:
        path = _get_module_paths(modules=["fake_module"])[0]
        assert path is None

    @staticmethod
    def test_should_raise_error_for_built_in_module() -> None:
        with pytest.raises(NotImplementedError) as exc_info:
            _ = _get_module_paths(modules=["sys"])
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


class TestFilterBySource:
    @staticmethod
    @pytest.fixture(
        name="mypy_upgrade_module",
        params=[
            str(p.relative_to(pathlib.Path(__file__).parents[1]))
            for p in pathlib.Path(__file__)
            .parents[1]
            .joinpath("src", "mypy_upgrade")
            .iterdir()
            if p.suffix == ".py"
        ],
    )
    def fixture_mypy_upgrade_module(request: pytest.FixtureRequest) -> str:
        mypy_upgrade_module: str = request.param
        return mypy_upgrade_module

    @staticmethod
    @pytest.mark.slow
    def test_should_only_include_selected_packages(
        parsed_errors: list[MypyError], packages_to_include: list[str]
    ) -> None:
        filtered_errors = filter_by_source(
            errors=parsed_errors,
            packages=packages_to_include,
            modules=[],
            files=[],
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
        filtered_errors = filter_by_source(
            errors=parsed_errors,
            packages=[],
            modules=modules_to_include,
            files=[],
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
        filtered_errors = filter_by_source(
            errors=parsed_errors,
            packages=[],
            modules=[],
            files=files_to_include,
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
        filtered_errors = filter_by_source(
            errors=parsed_errors,
            packages=packages_to_include,
            modules=modules_to_include,
            files=files_to_include,
        )

        to_include = (
            packages_to_include + modules_to_include + files_to_include
        )
        if to_include:
            assert all(
                any(path in error.filename for path in to_include)
                for error in filtered_errors
            )
        else:
            assert filtered_errors == parsed_errors

    @staticmethod
    def test_should_include_selected_package(mypy_upgrade_module: str) -> None:
        error = MypyError(mypy_upgrade_module, 1, 0, "", "")
        filtered_errors = filter_by_source(
            errors=[error],
            packages=["mypy_upgrade"],
            modules=[],
            files=[],
        )
        assert filtered_errors == [error]

    @staticmethod
    def test_should_include_selected_module(mypy_upgrade_module: str) -> None:
        error = MypyError(mypy_upgrade_module, 1, 0, "", "")
        module = ".".join(mypy_upgrade_module.split("/")[-2:]).rstrip(".py")
        filtered_errors = filter_by_source(
            errors=[error],
            packages=[],
            modules=[module],
            files=[],
        )
        assert filtered_errors == [error]

    @staticmethod
    def test_should_include_selected_file(mypy_upgrade_module: str) -> None:
        error = MypyError(mypy_upgrade_module, 1, 0, "", "")
        filtered_errors = filter_by_source(
            errors=[error],
            packages=[],
            modules=[],
            files=[mypy_upgrade_module],
        )
        assert filtered_errors == [error]

    @staticmethod
    def test_should_include_all_errors_when_modules_not_in_python_path(
        mypy_upgrade_module: str,
    ) -> None:
        error = MypyError(mypy_upgrade_module, 1, 0, "", "")
        filtered_errors = filter_by_source(
            errors=[error],
            packages=[],
            modules=["fake_module"],
            files=[mypy_upgrade_module],
        )
        assert filtered_errors == [error]

    @staticmethod
    def test_should_include_all_errors_when_packages_not_in_python_path(
        mypy_upgrade_module: str,
    ) -> None:
        error = MypyError(mypy_upgrade_module, 1, 0, "", "")
        filtered_errors = filter_by_source(
            errors=[error],
            packages=["fake_package"],
            modules=[],
            files=[mypy_upgrade_module],
        )
        assert filtered_errors == [error]


class TestFindUnsilenceableRegions:
    @staticmethod
    def test_should_return_explicitly_continued_lines() -> None:
        code = "\n".join(
            [
                "x = 1+\\",
                "1",
                "if x == 4:",
                "    return True",
            ]
        )
        stream = io.StringIO(code)
        tokens = list(tokenize.generate_tokens(stream.readline))
        comments = ["" for _ in code.splitlines()]
        regions = _find_unsilenceable_regions(tokens=tokens, comments=comments)
        expected = UnsilenceableRegion(1, 1)
        assert expected in regions

    @staticmethod
    def test_should_not_return_explicitly_continued_lines_in_comment() -> None:
        code = "x = 1 #\\"
        stream = io.StringIO(code)
        tokens = list(tokenize.generate_tokens(stream.readline))
        comments = ["#\\"]
        regions = _find_unsilenceable_regions(tokens=tokens, comments=comments)
        assert len(regions) == 0

    @staticmethod
    def test_should_return_multiline_string() -> None:
        code = "\n".join(
            [
                "x = '''Hi,",
                "this is a multiline",
                "string'''",
            ]
        )
        stream = io.StringIO(code)
        tokens = list(tokenize.generate_tokens(stream.readline))
        comments = ["" for _ in code.splitlines()]
        regions = _find_unsilenceable_regions(tokens=tokens, comments=comments)
        expected = UnsilenceableRegion(1, 3)
        assert expected in regions


class TestIsSafeToSilence:
    @staticmethod
    def test_should_return_false_if_error_in_explicitly_continued_line() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 1, 0, "", "")
        region = UnsilenceableRegion(1, 1)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence

    @staticmethod
    def test_should_return_false_if_error_in_explicitly_continued_line_and_col_offset_is_none() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 1, None, "", "")
        region = UnsilenceableRegion(1, 1)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence

    @staticmethod
    def test_should_return_false_if_error_in_multiline_string() -> None:
        error = MypyError("", 2, 0, "", "")
        region = UnsilenceableRegion(1, 3)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence

    @staticmethod
    def test_should_return_false_if_error_on_multiline_string_line_and_col_offset_is_none() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 2, None, "", "")
        region = UnsilenceableRegion(1, 3)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence

    @staticmethod
    def test_should_return_true_for_single_line_statement() -> None:
        error = MypyError("", 2, None, "", "")
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[]
        )
        assert safe_to_silence

    @staticmethod
    def test_should_return_false_for_error_before_multiline_string() -> None:
        error = MypyError("", 1, 0, "", "")
        region = UnsilenceableRegion(1, 3)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence

    @staticmethod
    def test_should_return_false_for_syntax_error() -> None:
        error = MypyError("", 1, 0, "", "syntax")
        region = UnsilenceableRegion(1, 3)
        safe_to_silence = _is_safe_to_silence(
            error=error, unsilenceable_regions=[region]
        )
        assert not safe_to_silence


class TestFilterBySilenceability:
    @staticmethod
    @pytest.fixture(name="single_line_tokens")
    def fixture_single_line_tokens() -> (
        Generator[tokenize.TokenInfo, None, None]
    ):
        code = "x = 1"
        reader = io.StringIO(code).readline
        return tokenize.generate_tokens(reader)

    @staticmethod
    @pytest.fixture(name="multiline_tokens")
    def fixture_multiline_tokens() -> (
        Generator[tokenize.TokenInfo, None, None]
    ):
        code = "x = '''\nstring\n'''"
        reader = io.StringIO(code).readline
        return tokenize.generate_tokens(reader)

    @staticmethod
    @pytest.fixture(name="explicitly_continued_line_tokens")
    def fixture_explicitly_continued_line_tokens() -> (
        Generator[tokenize.TokenInfo, None, None]
    ):
        code = "x = x\\\n+1\n"
        reader = io.StringIO(code).readline
        return tokenize.generate_tokens(reader)

    @staticmethod
    @pytest.mark.parametrize("line_no", [1, 2])
    def test_should_filter_error_within_multiline_string(
        line_no: int,
        multiline_tokens: Generator[tokenize.TokenInfo, None, None],
    ) -> None:
        error = MypyError("", line_no, 0, "", "")
        filtered_errors = filter_by_silenceability(
            errors=[error], comments=["", "", ""], tokens=multiline_tokens
        )
        assert error not in filtered_errors

    @staticmethod
    def test_should_include_error_at_end_of_multiline_string(
        multiline_tokens: Generator[tokenize.TokenInfo, None, None],
    ) -> None:
        error = MypyError("", 3, 0, "", "")
        filtered_errors = filter_by_silenceability(
            errors=[error], comments=["", "", ""], tokens=multiline_tokens
        )
        assert error in filtered_errors

    @staticmethod
    def test_should_filter_error_on_explicitly_continued_line(
        explicitly_continued_line_tokens: Generator[
            tokenize.TokenInfo, None, None
        ],
    ) -> None:
        error = MypyError("", 1, 0, "", "")
        filtered_errors = filter_by_silenceability(
            errors=[error],
            comments=["", "", ""],
            tokens=explicitly_continued_line_tokens,
        )
        assert error not in filtered_errors

    @staticmethod
    def test_should_not_change_line_number_for_single_line_errors(
        single_line_tokens: Generator[tokenize.TokenInfo, None, None]
    ) -> None:
        error = MypyError("", 1, 0, "", "")
        filtered_errors = filter_by_silenceability(
            errors=[error],
            comments=["", "", ""],
            tokens=single_line_tokens,
        )
        assert error in filtered_errors
