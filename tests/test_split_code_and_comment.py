import pytest

from mypy_upgrade.utils import split_code_and_comment

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


@pytest.mark.parametrize(
    ("code_line", "code_and_comment"),
    zip(CODE_LINES, CODE_AND_COMMENTS, strict=True),
)
def test_should_split_lines_into_code_and_comment_correctly(
    code_line: str, code_and_comment: tuple[str, str]
):
    split = split_code_and_comment(code_line)
    assert split == code_and_comment
