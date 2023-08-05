from __future__ import annotations

import io
import sys
import tokenize

import pytest

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.utils import (
    correct_line_numbers,
    find_safe_end_line,
    find_safe_end_line_with_multiline_comment,
    find_unsilenceable_lines,
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


class TestFindUnsilenceableLines:
    @staticmethod
    def test_should_return_tokens_on_explicitly_continued_lines():
        code = "\n".join(
            [
                "x = 1+\\",
                "1",
                "if x == 4:",
                "    return True",
            ]
        )
        stream = io.StringIO(code)
        tokens = find_unsilenceable_lines(stream)
        assert any(token.end[0] == 1 for token in tokens)

    @staticmethod
    def test_should_only_return_string_token_for_explicitly_continued_string():
        code = "\n".join(
            [
                "x = '\\",
                "1'",
            ]
        )
        stream = io.StringIO(code)
        tokens = find_unsilenceable_lines(stream)
        assert all(token.exact_type == tokenize.STRING for token in tokens)

    @staticmethod
    def test_should_return_tokens_in_multiline_strings1():
        code = "\n".join(
            [
                "x = '''Hi,",
                "this is a multiline",
                "string'''",
            ]
        )
        stream = io.StringIO(code)
        tokens = find_unsilenceable_lines(stream)
        assert any(t.start[0] == 1 for t in tokens)
        assert any(t.end[0] == 3 for t in tokens)

    @staticmethod
    def test_should_return_tokens_in_multiline_strings2():
        code = "\n".join(
            [
                "comment = '\\",
                "this is a\\",
                "multiline string'",
            ]
        )
        stream = io.StringIO(code)
        tokens = find_unsilenceable_lines(stream)
        assert any(t.start[0] == 1 for t in tokens)
        assert any(t.end[0] == 3 for t in tokens)


class TestFindSafeEndLineWithMultilineComment:
    @staticmethod
    def test_should_return_none_if_error_in_multiline_comment() -> None:
        error = MypyError("", 0, 2, "", "")
        code = "\n".join(["x = '''", "string", "'''"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line_with_multiline_comment(
            error, same_line_string_tokens
        )
        assert end_line is None

    @staticmethod
    def test_should_return_end_line_if_error_before_isolated_multiline_comment() -> (
        None
    ):
        error = MypyError("", 0, 1, "", "")
        code = "\n".join(["x = '''", "string", "'''"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line_with_multiline_comment(
            error, same_line_string_tokens
        )
        assert end_line == 3

    @staticmethod
    def test_should_return_end_line_if_error_at_end_of_isolated_multiline_comment() -> (
        None
    ):
        error = MypyError("", 0, 3, "", "")
        code = "\n".join(["x = '''", "string", "'''"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line_with_multiline_comment(
            error, same_line_string_tokens
        )
        assert end_line == 3

    @staticmethod
    def test_should_second_end_line_if_error_before_chained_multiline_comment() -> (
        None
    ):
        error = MypyError("", 0, 1, "", "")
        code = "\n".join(["x = '''", "string", "'''.join('''", "", "''')"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line_with_multiline_comment(
            error, same_line_string_tokens
        )
        assert end_line == 5


class TestFindSafeEndLine:
    @staticmethod
    def test_should_return_none_if_error_in_explicitly_continued_line() -> (
        None
    ):
        error = MypyError("", 0, 1, "", "")
        code = "\n".join(["x = 1+\\", "1"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.start[0] == t.end[0] == 1
        ]
        end_line = find_safe_end_line(error, same_line_string_tokens)
        assert end_line is None

    @staticmethod
    def test_should_return_none_if_error_in_multiline_string() -> None:
        error = MypyError("", 0, 2, "", "")
        code = "\n".join(["x = f'''", "1{format}", "'''"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.start[0] <= 2 <= t.end[0]
        ]
        end_line = find_safe_end_line(error, same_line_string_tokens)
        assert end_line is None

    @staticmethod
    def test_should_return_same_line_for_single_line_statement() -> None:
        error = MypyError("", 0, 1, "", "")
        code = "x = 5"
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line(error, same_line_string_tokens)
        assert end_line == 1

    @staticmethod
    def test_should_return_end_line_for_error_before_multiline_string() -> (
        None
    ):
        error = MypyError("", 0, 1, "", "")
        code = "\n".join(["x = '''", "", "'''"])
        reader = io.StringIO(code).readline
        same_line_string_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.exact_type == tokenize.STRING
        ]
        end_line = find_safe_end_line(error, same_line_string_tokens)
        assert end_line == 3


class TestCorrectLineNumbers:
    @staticmethod
    def test_should_correct_line_number_to_end_line_for_error_on_first_line_and_before_multiline_string():
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 0, 1, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 3
        assert len(not_added) == 0

    @staticmethod
    def test_should_separate_error_for_error_on_first_line_inside_multiline_string():
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 5, 1, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 1
        assert len(not_added) == 1

    @staticmethod
    def test_should_return_same_line_for_error_on_last_line_of_multiline_string():
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 0, 3, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 3
        assert len(not_added) == 0

    @staticmethod
    def test_should_correct_line_number_to_next_end_line_for_error_last_line_of_chained_multiline_string():
        code = "\n".join(
            ["x = '''", "string", "'''.join('''", "chain", "''')"]
        )
        stream = io.StringIO(code)
        error = MypyError("", 0, 3, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 5
        assert len(not_added) == 0

    @staticmethod
    def test_should_separate_error_inside_multiline_string():
        code = "\n".join(["x = '''", "string", "'''"])
        stream = io.StringIO(code)
        error = MypyError("", 0, 2, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 2
        assert len(not_added) == 1

    @staticmethod
    def test_should_separate_error_on_explicitly_continued_line():
        code = "\n".join(["x = 1 +\\", "1"])
        stream = io.StringIO(code)
        error = MypyError("", 0, 1, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert len(corrected_errors) == 0
        assert not_added[0].line_no == 1
        assert len(not_added) == 1

    @staticmethod
    def test_should_not_change_line_number_for_single_line_errors():
        code = "x = 1"
        stream = io.StringIO(code)
        error = MypyError("", 0, 1, "", "")
        corrected_errors, not_added = correct_line_numbers(stream, [error])
        assert corrected_errors
        assert corrected_errors[0].line_no == 1
        assert len(not_added) == 0
