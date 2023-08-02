# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import tokenize


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
            return line, ""

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

    return python_code, python_comment
