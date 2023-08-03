# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

from collections.abc import Iterable

from typing_extensions import Literal  # import from typing for Python 3.8+

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
    suffix: Literal["description"] | None,
) -> str:
    """Silences the given error on a line with an error code-specific comment.

    Args:
        line: a string containing the line.
        error_code: a string representing the mypy error code.
        description: a string representing a description of the error.
    Returns:
        The line with a type error suppression comment.
    """
    unused_ignore = None
    error_codes = []
    descriptions = []
    for error in errors:
        if error.error_code == "unused-ignore":
            unused_ignore = error  # there should only be one
        else:
            error_codes.append(error.error_code)
            descriptions.append(error.description)

    python_code, comment = split_code_and_comment(line.rstrip())

    if unused_ignore:
        codes_to_remove = description_to_type_ignore(unused_ignore.description)
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

    if suffix == "description" and descriptions:
        updated_line += f" # {', '.join(descriptions)}"

    return updated_line + "\n"
