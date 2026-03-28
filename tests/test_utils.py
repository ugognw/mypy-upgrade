from __future__ import annotations

import io
import tokenize

import pytest

from mypy_upgrade.utils import CommentSplitLine, split_into_code_and_comment

CODE_LINES = [
    "x = 5\n",
    "if x == '4':\n",
    "\n",
    "\r\n",
    "This has an empty comment#\n",
    "This has an empty comment #\n",
    "This has a comment# here\n",
    "This has a comment # here\n",
    "This has one comment that looks like two # here # and here\n",
    "This has a 'comment' in a string '# fake comment'",
]

CODE_AND_COMMENTS = [
    ("x = 5", "", "\n"),
    ("if x == '4':", "", "\n"),
    ("", "", "\n"),
    ("", "", "\r\n"),
    ("This has an empty comment", "#", "\n"),
    ("This has an empty comment ", "#", "\n"),
    ("This has a comment", "# here", "\n"),
    ("This has a comment ", "# here", "\n"),
    ("This has one comment that looks like two ", "# here # and here", "\n"),
    ("This has a 'comment' in a string '# fake comment'", "", ""),
]


class TestSplitIntoCodeAndComment:
    @staticmethod
    @pytest.fixture(name="split_lines", scope="class")
    def fixture_split_lines() -> list[CommentSplitLine]:
        code = "".join(CODE_LINES)
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        return split_into_code_and_comment(source=code, tokens=tokens)

    @staticmethod
    def test_should_return_all_code(
        split_lines: list[CommentSplitLine],
    ) -> None:
        for i, line in enumerate(split_lines):
            assert line.code + line.comment + line.newline == CODE_LINES[i]

            assert line.code == CODE_AND_COMMENTS[i][0]
            assert line.comment == CODE_AND_COMMENTS[i][1]
            assert line.newline == CODE_AND_COMMENTS[i][2]
