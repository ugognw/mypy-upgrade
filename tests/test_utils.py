from __future__ import annotations

import io
import sys

import pytest

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.utils import correct_line_numbers, split_code_and_comment

CODE_LINES = [
    "x = 5\n",
    "if x == '4':\n",
    "\n",
    "This has an empty comment#\n",
    "This has an empty comment #\n",
    "This has a comment# here\n",
    "This has a comment # here\n",
    "This has one comment that looks like two # here # and here\n",
]

CODE_AND_COMMENTS = [
    ("x = 5\n", ""),
    ("if x == '4':\n", ""),
    ("\n", ""),
    ("This has an empty comment", "#\n"),
    ("This has an empty comment ", "#\n"),
    ("This has a comment", "# here\n"),
    ("This has a comment ", "# here\n"),
    ("This has one comment that looks like two ", "# here # and here\n"),
]


class TestSplitCodeAndComment:
    if sys.version_info < (3, 10):
        CODE_LINES_AND_CODE_AND_COMMENTS = zip(CODE_LINES, CODE_AND_COMMENTS)
    else:
        CODE_LINES_AND_CODE_AND_COMMENTS = zip(
            CODE_LINES, CODE_AND_COMMENTS, strict=True
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("code_line", "code_and_comment"),
        CODE_LINES_AND_CODE_AND_COMMENTS,
    )
    def test_should_split_lines_into_code_and_comment_correctly(
        code_line: str, code_and_comment: tuple[str, str]
    ) -> None:
        split = split_code_and_comment(code_line)
        stripped_code_and_comment = (
            code_and_comment[0].strip(),
            code_and_comment[1],
        )
        assert split == stripped_code_and_comment


LINES = [
    "x = 4",  # line 1
    "if x == 2:",
    '    print("2")',
    "else:",
    "    for x in range(0):",
    "        pass",
    "",
    "list(",
    "    [1, 2, 3]",
    ")",
    'text = """',  # line 11
    "This is",
    "a multiline",
    "comment",
    '"""',  # line 15
]

SAMPLE_CODE = "\n".join(LINES)


@pytest.fixture(name="single_line_no", params=range(1, 11), scope="class")
def fixture_single_line_no(request: pytest.FixtureRequest) -> int:
    single_line_no: int = request.param
    return single_line_no


@pytest.fixture(
    name="multi_line_no", params=range(11, len(LINES) + 1), scope="class"
)
def fixture_multi_line_no(request: pytest.FixtureRequest) -> int:
    multi_line_no: int = request.param
    return multi_line_no


@pytest.fixture(name="errors", scope="class")
def fixture_errors(single_line_no: int, multi_line_no: int) -> list[MypyError]:
    return [
        MypyError("", single_line_no, "", ""),
        MypyError("", multi_line_no, "", ""),
    ]


@pytest.fixture(name="line_corrected_errors_and_lines", scope="class")
def fixture_line_corrected_errors_and_lines(
    errors: list[MypyError],
) -> tuple[list[MypyError], list[str]]:
    stream = io.StringIO(SAMPLE_CODE)
    return correct_line_numbers(stream, errors)


class TestCorrectLineNumbers:
    @staticmethod
    def test_should_return_same_line_of_single_line_statement(
        errors: list[MypyError],
        line_corrected_errors_and_lines: tuple[list[MypyError], list[str]],
    ) -> None:
        line_corrected_errors, _ = line_corrected_errors_and_lines
        assert line_corrected_errors[0].line_no == errors[0].line_no

    @staticmethod
    def test_should_return_end_line_of_multiline_statement(
        line_corrected_errors_and_lines: tuple[list[MypyError], list[str]]
    ) -> None:
        line_corrected_errors, _ = line_corrected_errors_and_lines
        assert line_corrected_errors[1].line_no == len(LINES)

    @staticmethod
    def test_should_return_lines_of_stream(
        line_corrected_errors_and_lines: tuple[list[MypyError], list[str]]
    ) -> None:
        _, lines = line_corrected_errors_and_lines
        assert all(
            line in lines for line in SAMPLE_CODE.splitlines(keepends=True)
        )
