from __future__ import annotations

import io
import sys

import pytest

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.utils import (
    UnsilenceableRegion,
    correct_line_numbers,
    find_safe_end_line,
    find_unsilenceable_regions,
    split_code_and_comment,
)

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
        regions = find_unsilenceable_regions(stream)
        expected = UnsilenceableRegion((1, 0), (1, 8))
        assert expected in regions

    @staticmethod
    def test_should_not_return_explicitly_continued_lines_in_comment() -> None:
        code = "x = 1 #\\"
        stream = io.StringIO(code)
        regions = find_unsilenceable_regions(stream)
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
        regions = find_unsilenceable_regions(stream)
        expected = UnsilenceableRegion((1, 4), (3, 9))
        assert expected in regions


class TestFindSafeEndLine:
    @staticmethod
    def test_should_return_negative_1_if_error_in_explicitly_continued_line() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 1, 0, "", "")
        region = UnsilenceableRegion((1, 0), (1, 1))
        end_line = find_safe_end_line(error, [region])
        assert end_line == -1

    @staticmethod
    def test_should_return_negative_1_if_error_in_explicitly_continued_line_and_col_offset_is_none() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 1, None, "", "")
        region = UnsilenceableRegion((1, 0), (1, -1))
        end_line = find_safe_end_line(error, [region])
        assert end_line == -1

    @staticmethod
    def test_should_return_negative_1_if_error_in_multiline_string() -> None:
        error = MypyError("", 2, 0, "", "")
        region = UnsilenceableRegion((1, 0), (3, 0))
        end_line = find_safe_end_line(error, [region])
        assert end_line == -1

    @staticmethod
    def test_should_return_negative_1_if_error_on_multiline_string_line_and_col_offset_is_none() -> (  # noqa: E501
        None
    ):
        error = MypyError("", 2, None, "", "")
        region = UnsilenceableRegion((1, 0), (3, 0))
        end_line = find_safe_end_line(error, [region])
        assert end_line == -1

    @staticmethod
    def test_should_return_same_line_for_single_line_statement() -> None:
        error = MypyError("", 2, None, "", "")
        end_line = find_safe_end_line(error, [])
        assert end_line == 2

    @staticmethod
    def test_should_return_negative_1_for_error_before_multiline_string() -> (
        None
    ):
        error = MypyError("", 1, 0, "", "")
        region = UnsilenceableRegion((1, 1), (3, 0))
        end_line = find_safe_end_line(error, [region])
        assert end_line == -1


class TestCorrectLineNumbers:
    @staticmethod
    def test_should_separate_error_for_error_on_first_line_and_before_multiline_string() -> (  # noqa: E501
        None
    ):
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 1, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 1
        assert len(not_added) == 1

    @staticmethod
    def test_should_separate_error_for_error_on_first_line_inside_multiline_string() -> (  # noqa: E501
        None
    ):
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 1, 5, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 1
        assert len(not_added) == 1

    @staticmethod
    def test_should_return_same_line_for_error_on_last_line_of_multiline_string() -> (  # noqa: E501
        None
    ):
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 3, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 3
        assert len(not_added) == 0

    @staticmethod
    def test_should_separate_error_inside_multiline_string() -> None:
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 2, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 2
        assert len(not_added) == 1

    @staticmethod
    @pytest.mark.skipif(
        sys.version_info >= (3, 12),
        reason=(
            "line continuation characters within function calls is "
            "not valid syntax in Python 3.12+"
        ),
    )
    def test_should_separate_error_before_multiline_string_if_preceding_chained_explicitly_continued_line() -> (  # noqa: E501
        None
    ):
        code = "\n".join(["x = '''", "string", "'''.join('\\", "chain", "')"])
        stream = io.StringIO(code)
        error = MypyError("", 1, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert len(not_added) == 1

    @staticmethod
    def test_should_separate_error_on_explicitly_continued_line() -> None:
        code = "\n".join(["x = 1 +\\", "1"])
        stream = io.StringIO(code)
        error = MypyError("", 1, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 1
        assert len(not_added) == 1

    @staticmethod
    def test_should_not_change_line_number_for_single_line_errors() -> None:
        code = "x = 1"
        stream = io.StringIO(code)
        error = MypyError("", 1, 0, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 1
        assert len(not_added) == 0
