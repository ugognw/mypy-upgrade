# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import tokenize
from collections.abc import Iterable
from typing import TextIO

from mypy_upgrade.parsing import MypyError


def split_code_and_comment(line: str) -> tuple[str, str]:
    """Split a line of code into the code part and comment part."""
    reader = io.StringIO(line).readline

    try:
        comment_tokens = [
            t
            for t in tokenize.generate_tokens(reader)
            if t.type == tokenize.COMMENT
        ]
        if not comment_tokens:
            return line.rstrip(), ""

        comment_token = comment_tokens[0]
        python_code = line[0 : comment_token.start[1]]
        python_comment = line[comment_token.start[1] :]
    except tokenize.TokenError:  # compromise for multi-line statements
        comment_start = line.find("#")
        if comment_start >= 0:
            python_code = line[0:comment_start]
            python_comment = line[comment_start:]
        else:
            python_code, python_comment = (line, "")

    return python_code.rstrip(), python_comment


def correct_line_numbers(
    stream: TextIO, errors: Iterable[MypyError]
) -> tuple[list[MypyError], list[str]]:
    """Correct the line numbers of MypyErrors considering multiline statements.

    Args:
        stream: A text stream from which the line numbers of provided errors
            are to be corrected.
        errors: The errors whose line numbers are to be corrected.

    Returns:
        A 2-tuple whose first entry is a copy of the original list of MyPy
        errors with line numbers corrected and whose second entry is a list of
        the lines in the supplied stream.
    """
    reader = stream.readline
    tokens = list(tokenize.generate_tokens(reader))
    line_corrected_errors = []
    for error in errors:
        same_line_tokens = []
        for t in tokens:
            if (
                t.start[0] <= error.line_no <= t.end[0]
                and t.exact_type != tokenize.ENDMARKER
            ):
                same_line_tokens.append(t.end[0])
        line_no = max(same_line_tokens)
        line_corrected_errors.append(
            MypyError(
                error.filename, line_no, error.description, error.error_code
            )
        )

    lines = tokenize.untokenize(tokens).splitlines(keepends=True)
    return line_corrected_errors, lines
