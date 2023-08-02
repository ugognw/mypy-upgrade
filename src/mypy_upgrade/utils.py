import io
import tokenize

from mypy_upgrade.parsing import MypyError


def filename_and_line_number(error: MypyError) -> tuple[str, int]:
    return error.filename, error.line_no


def split_code_and_comment(line: str) -> tuple[str, str]:
    """Split a line of code into the code part and comment part."""
    reader = io.StringIO(line).readline

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
    return python_code, python_comment
