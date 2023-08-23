from __future__ import annotations

import io
import tokenize

import pytest

from mypy_upgrade.utils import CommentSplitLine, split_into_code_and_comment

CODE_LINES = [
    "x = 5\n",
    "if x == '4':\n",
    "\n",
    "This has an empty comment#\n",
    "This has an empty comment #\n",
    "This has a comment# here\n",
    "This has a comment # here\n",
    "This has one comment that looks like two # here # and here\n",
    "This has a 'comment' in a string '# fake comment'",
]

CODE_AND_COMMENTS = [
    ("x = 5", ""),
    ("if x == '4':", ""),
    ("", ""),
    ("This has an empty comment", "#"),
    ("This has an empty comment ", "#"),
    ("This has a comment", "# here"),
    ("This has a comment ", "# here"),
    ("This has one comment that looks like two ", "# here # and here"),
    ("This has a 'comment' in a string '# fake comment'", ""),
]


class TestSplitIntoCodeAndComment:
    @staticmethod
    @pytest.fixture(name="split_lines", scope="class")
    def fixture_split_lines() -> list[CommentSplitLine]:
        code = "".join(CODE_LINES)
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        return split_into_code_and_comment(code, tokens)

    @staticmethod
    def test_should_return_all_code(
        split_lines: list[CommentSplitLine],
    ) -> None:
        assert all(
            line.code == CODE_AND_COMMENTS[i][0]
            for i, line in enumerate(split_lines)
        )

    @staticmethod
    def test_should_return_all_comments(
        split_lines: list[CommentSplitLine],
    ) -> None:
        assert all(
            line.comment == CODE_AND_COMMENTS[i][1]
            for i, line in enumerate(split_lines)
        )
