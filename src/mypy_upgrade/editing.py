"""This module defines comment editing utilities."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import re
from collections.abc import Collection

from mypy_upgrade.parsing import string_to_error_codes


def add_type_ignore_comment(comment: str, error_codes: list[str]) -> str:
    """Add a `type: ignore` comment with error codes to in-line comment.

    Args:
        comment: a string representing a comment in which to add a `type:
            ignore` comment.
        error_codes: the error codes to add to the `type: ignore` comment.

    Returns:
        A copy of the original comment with a `type: ignore[error-code]`
        comment added
    """
    type_ignore = re.compile(r"# type\s*:\s*ignore(\[[a-z, \-]*\])?")
    match = type_ignore.match(comment)
    existing_codes = string_to_error_codes(match.string if match else "")
    error_codes.extend(existing_codes)
    codes = f'[{", ".join(sorted({*error_codes}))}]' if error_codes else ""
    if match:
        return type_ignore.sub(f"# type: ignore{codes}", comment).rstrip()

    return f"# type: ignore{codes} {comment}".rstrip()


def format_type_ignore_comment(comment: str) -> str:
    """Remove excess whitespace and commas from a `"type: ignore"` comment."""
    type_ignore = re.compile(
        r"type\s*:\s*ignore(\[(?P<error_codes>[a-z, \-]*)\])?"
    )
    match = type_ignore.search(comment)

    # Format existing error codes
    if match is None:
        return comment.rstrip()

    error_codes_section = match.group("error_codes") or ""
    comma_separated_codes = error_codes_section.replace(" ", "")
    error_codes = [e for e in comma_separated_codes.split(",") if e]

    codes = f'[{", ".join(error_codes)}]' if error_codes else ""
    return type_ignore.sub(f"type: ignore{codes}", comment, count=1).rstrip()


def remove_unused_type_ignore_comments(
    comment: str, codes_to_remove: Collection[str]
) -> str:
    """Remove specified error codes from a comment string.

    Args:
        comment: a string whose "type: ignore" codes are to be removed.
        codes_to_remove: a collection of strings which represent mypy error
            codes.

    Returns:
        A copy of the original string with the specified error codes removed.
    """
    type_ignore = re.compile(
        r"#\s*type\s*:\s*ignore(\[(?P<error_code>[a-z, \-]+)\])?"
    )
    if "*" in codes_to_remove:
        return type_ignore.sub("", comment)

    match = type_ignore.search(comment)
    old_codes = match.group("error_code") or "" if match is not None else ""
    new_codes = old_codes
    for code in codes_to_remove:
        new_codes = new_codes.replace(code, "")
    return type_ignore.sub(f"type: ignore[{new_codes}]", comment, count=1)
