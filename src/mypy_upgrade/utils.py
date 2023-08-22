"""This module defines general utilities and the UnsilenceableRegion class."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import tokenize
from typing import NamedTuple, TextIO


class CommentSplitLine(NamedTuple):
    code: str
    comment: str


def split_into_code_and_comment(line, comments) -> tuple[str, str]:
    comment = ""
    for comment_ in comments:
        if comment_.line == line:
            comment = comment_.string
            break

    python_code = line.replace(comment, "")
    return python_code.rstrip(), comment.rstrip()


def get_lines_and_tokens(
    stream: TextIO,
) -> tuple[list[str], list[tokenize.TokenInfo]]:
    """Extract lines and tokenize text stream.

    Args:
        stream: a TextIO object.

    Returns:
        A 2-tuple whose first entry is a list of all lines in `stream` and
        whose second entry is a list of `TokenInfo` objects representing the
        tokens in `stream`.
    """
    lines = stream.readlines()
    copied_stream = io.StringIO("".join(lines))
    tokens = []
    for token in tokenize.generate_tokens(copied_stream.readline):
        tokens.append(token)

    return lines, tokens
