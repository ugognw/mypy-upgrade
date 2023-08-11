"""This module defines the `silence_errors` function."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import sys
from collections.abc import Iterable

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.editing import (
    add_type_ignore_comment,
    format_type_ignore_comment,
    remove_unused_type_ignore_comment,
)
from mypy_upgrade.parsing import MypyError, string_to_error_codes
from mypy_upgrade.utils import split_code_and_comment


def _extract_error_details(
    errors: Iterable[MypyError],
) -> tuple[list[str], list[str], MypyError | None, bool]:
    error_codes = []
    descriptions = []
    unused_ignore = None
    ignore_without_code = False
    for error in errors:
        if error.error_code == "unused-ignore":
            unused_ignore = error  # there should only be one error per line
        elif error.error_code == "ignore-without-code":
            suggested_error_codes = string_to_error_codes(error.message)
            if suggested_error_codes:
                ignore_without_code = True
                for error_code in suggested_error_codes:
                    if error_code not in error_codes:
                        error_codes.append(error_code)
                        descriptions.append("")
            # 0 error codes in error.message = unused `type: ignore`
            else:
                error_ = MypyError(
                    error.filename,
                    error.line_no,
                    error.col_offset,
                    "",
                    "unused-ignore",
                )
                unused_ignore = error_
        elif error.error_code not in error_codes:
            error_codes.append(error.error_code)
            descriptions.append(error.message)

    return error_codes, descriptions, unused_ignore, ignore_without_code


def silence_errors(
    line: str,
    errors: Iterable[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> str:
    """Silences the given error on a line with an error code-specific comment.

    Args:
        line: a string containing the line.
        error: an `Iterable` in which each entry is a `MypyError` to be
            silenced.
        description_style: a string specifying the style of the description of
            errors.
        fix_me: a string specifying a "fix me" message to be appended after the
            silencing comment.
    Returns:
        The line with a type error suppression comment.
    """
    (
        codes_to_add,
        descriptions,
        unused_ignore,
        ignore_without_code,
    ) = _extract_error_details(errors)

    python_code, comment = split_code_and_comment(line.rstrip())

    if unused_ignore or ignore_without_code:
        if unused_ignore:
            codes_to_remove = string_to_error_codes(unused_ignore.message)
        else:
            codes_to_remove = ()
        pruned_comment = remove_unused_type_ignore_comment(
            comment, codes_to_remove
        )
        cleaned_comment = format_type_ignore_comment(pruned_comment)
    else:
        cleaned_comment = comment

    if codes_to_add:
        final_comment = add_type_ignore_comment(
            cleaned_comment,
            codes_to_add,
        )
    else:
        final_comment = cleaned_comment

    updated_line = f"{python_code}  {final_comment}".rstrip()

    if fix_me:
        updated_line += f" # {fix_me}"

    if description_style == "full" and descriptions:
        updated_line += f" # {', '.join(descriptions)}"

    return updated_line + "\n"
