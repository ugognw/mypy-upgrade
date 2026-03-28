"""This module defines general utilities and the UnsilenceableRegion class."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import tokenize
from collections.abc import Iterable
from typing import NamedTuple


class CommentSplitLine(NamedTuple):
    code: str
    comment: str
    newline: str


def split_into_code_and_comment(
    *, source: str, tokens: Iterable[tokenize.TokenInfo]
) -> list[CommentSplitLine]:
    """Split lines of source code into code and comments.

    Args:
        source: a string representing source code.
        tokens: an iterable containing the `TokenInfo` objects generated from
            tokenizing `source`.

    Returns:
        A list of all lines in `source` (split into code and comment) and
        whose second entry is a list of `TokenInfo` objects representing the
        tokens in `source`.
    """
    code_lines = source.splitlines()
    comments = [""] * len(code_lines)
    newlines = ["\n"] * len(code_lines)

    line = 0
    for token in tokens:
        if token.exact_type == tokenize.COMMENT:
            line = token.start[0] - 1
            comments[line] = token.string
            code_lines[line] = code_lines[line][: token.start[1]]
        elif token.exact_type in (tokenize.NEWLINE, tokenize.NL):
            line = token.start[0] - 1
            newlines[line] = token.string

    lines = [
        CommentSplitLine(code, comment, newline)
        for code, comment, newline in zip(code_lines, comments, newlines)
    ]

    return lines
