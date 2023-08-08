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
    remove_unused_type_ignore,
)
from mypy_upgrade.parsing import MypyError, description_to_type_ignore
from mypy_upgrade.utils import split_code_and_comment


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
    unused_ignore = None
    error_codes = []
    descriptions = []
    for error in errors:
        if error.error_code == "unused-ignore":
            unused_ignore = error  # there should only be one
        elif error.error_code not in error_codes:
            error_codes.append(error.error_code)
            descriptions.append(error.message)

    python_code, comment = split_code_and_comment(line.rstrip())

    if unused_ignore:
        codes_to_remove = description_to_type_ignore(unused_ignore.message)
        pruned_comment = remove_unused_type_ignore(comment, codes_to_remove)
        cleaned_comment = format_type_ignore_comment(pruned_comment)
    else:
        cleaned_comment = comment

    if error_codes:
        final_comment = add_type_ignore_comment(
            cleaned_comment,
            error_codes,
        )
    else:
        final_comment = cleaned_comment

    updated_line = f"{python_code}  {final_comment}".rstrip()

    if fix_me:
        updated_line += f" # {fix_me.strip()}"

    if description_style == "full" and descriptions:
        updated_line += f" # {', '.join(descriptions)}"

    return updated_line + "\n"
