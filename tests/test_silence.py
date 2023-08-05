from __future__ import annotations

import sys
from collections.abc import Iterable

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.silence import silence_errors

CODE_SNIPPETS = [
    "if x == 5:",
    ")",
]

INDENTS = ["", "    "]

TYPE_IGNORE_COMMENTS = ["", "# type: ignore", "# type: ignore[override]"]

COMMENT_SUFFIXES = ["\n", "# noqa\n"]


@pytest.fixture(name="indent", params=INDENTS, scope="class")
def fixture_indent(request: pytest.FixtureRequest) -> str:
    indent: str = request.param
    return indent


@pytest.fixture(name="code_snippet", params=CODE_SNIPPETS, scope="class")
def fixture_code_snippet(request: pytest.FixtureRequest) -> str:
    code_snippet: str = request.param
    return code_snippet


@pytest.fixture(name="code", scope="class")
def fixture_code(code_snippet: str, indent: str) -> str:
    return indent + code_snippet


@pytest.fixture(
    name="type_ignore_comment", params=TYPE_IGNORE_COMMENTS, scope="class"
)
def fixture_type_ignore_comment(request: pytest.FixtureRequest) -> str:
    code_snippet: str = request.param
    return code_snippet


@pytest.fixture(name="comment_suffix", params=COMMENT_SUFFIXES, scope="class")
def fixture_comment_suffix(request: pytest.FixtureRequest) -> str:
    comment_suffix: str = request.param
    return comment_suffix


@pytest.fixture(name="comment", scope="class")
def fixture_comment(type_ignore_comment: str, comment_suffix: str) -> str:
    return type_ignore_comment + comment_suffix


@pytest.fixture(name="line", scope="class")
def fixture_line(code: str, comment: str) -> str:
    return code + comment


@pytest.fixture(name="errors_to_add")
def fixture_errors_to_add(type_ignore_comment: str) -> Iterable[MypyError]:
    errors_to_add = [
        MypyError(
            "ase/visualize/paraview_script.py",
            0,
            1,
            "Function is missing a return type annotation",
            "no-untyped-def",
        ),
        MypyError(
            "ase/lattice/bravais.py",
            0,
            72,
            '"Bravais" has no attribute "get_lattice_constant"',
            "attr-defined",
        ),
        MypyError(
            "ase/io/octopus/input.py",
            0,
            318,
            'Incompatible types in assignment (expression has type "None", '
            'variable has type "list[int]")',
            "assignment",
        ),
    ]
    if "type: ignore" in type_ignore_comment:
        placeholder = "[override]" if "override" in type_ignore_comment else ""
        errors_to_add.append(
            MypyError(
                "",
                0,
                1,
                f'Unused "type: ignore{placeholder}" comment',
                "unused-ignore",
            )
        )

    return (error for error in errors_to_add)


@pytest.fixture(name="suffix", params=("description", ""), scope="class")
def fixture_suffix(request: pytest.FixtureRequest) -> str:
    suffix: str = request.param
    return suffix


@pytest.fixture(name="silenced_line")
def fixture_silenced_line(
    line: str,
    errors_to_add: Iterable[MypyError],
    suffix: Literal["description", ""],
) -> str:
    return silence_errors(line, errors_to_add, suffix if suffix else None)


class TestSilenceErrors:
    @staticmethod
    def test_should_place_all_non_unused_ignore_errors_in_comment(
        silenced_line: str, errors_to_add: Iterable[MypyError]
    ) -> None:
        assert all(
            error.error_code in silenced_line
            for error in errors_to_add
            if error.error_code != "unused-ignore"
        )

    @staticmethod
    def test_should_place_type_ignore_at_beginning_of_comment(
        silenced_line: str,
    ) -> None:
        comment_start = silenced_line.find("#")
        if comment_start > -1:
            assert silenced_line[comment_start:].startswith("# type: ignore")
        else:
            pytest.skip("no type ignore comment")

    @staticmethod
    def test_should_preserve_indent(silenced_line: str, indent: str) -> None:
        assert silenced_line.startswith(indent)

    @staticmethod
    def test_should_end_line_with_newline(
        silenced_line: str,
    ) -> None:
        assert silenced_line.endswith("\n")

    @staticmethod
    def test_should_preserve_existing_suffix(
        silenced_line: str, comment_suffix: str
    ) -> None:
        assert comment_suffix.strip() in silenced_line
