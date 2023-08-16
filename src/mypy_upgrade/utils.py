"""This module defines general utilities and the UnsilenceableRegion class."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import tokenize
from collections.abc import Iterable, Sequence
from typing import NamedTuple, TextIO

from mypy_upgrade.parsing import MypyError


class UnsilenceableRegion(NamedTuple):
    """A region within a source code that cannot be silenced by an inline
    comment.

    Attributes:
        start: a 2-tuple representing the start of the unsilenceable region
            whose first entry is the start line (1-indexed) and whose second
            entry is the start column offset.
        end: a 2-tuple representing the end of the unsilenceable region
            whose first entry is the end line (1-indexed) and whose second
            entry is the end column offset.

        When start[0] = end[0], it is interpreted that the Unsilenceable
        region is an explicitly continued line.
    """

    start: tuple[int, int]  # line, column
    end: tuple[int, int]  # line, column


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
    lines = []
    tokens = []
    for token in tokenize.generate_tokens(stream.readline):
        tokens.append(token)
        if token.line not in lines:
            lines.append(token.line)

    return lines, tokens


def find_unsilenceable_regions(
    tokens: Iterable[tokenize.TokenInfo],
    comments: Sequence[tokenize.TokenInfo],
) -> list[UnsilenceableRegion]:
    """Find the regions encapsulated by line continuation characters or
    by multiline strings

    Args:
        tokens: an `Iterable` of `tokenize.TokenInfo` instances.
        comments: an `Iterable` of `tokenize.TokenInfo` instances which are
            `tokenize.COMMENT`'s.

    Returns:
        A list of UnsilenceableRegion objects.

        Multiline strings are represented by UnsilienceableRegion objects
        whose first entries in their `start` and `end` attributes are
        different. Explicitly continued lines are represented by
        UnsilienceableRegion objects whose first entries in their `start` and
        `end` attributes are the same.
    """
    unsilenceable_regions = []
    for token in tokens:
        if (
            token.start[0] != token.end[0]
            and token.exact_type == tokenize.STRING
        ):
            region = UnsilenceableRegion(token.start, token.end)
            unsilenceable_regions.append(region)
        elif token.line.rstrip("\r\n").endswith("\\") and not any(
            comment.line == token.line for comment in comments
        ):
            start = token.end[0], 0
            end = token.end[0], len(token.line)
            region = UnsilenceableRegion(start, end)
            unsilenceable_regions.append(region)

    return unsilenceable_regions


def find_safe_end_line(
    error: MypyError, unsilenceable_regions: Iterable[UnsilenceableRegion]
) -> int:
    """Find a syntax-safe line on which to place an error suppression comment
    for the given error.

    Args:
        error: a `MypyError` for which a type error suppression comment is to
            placed.
        unsilenceable_regions: an `Iterable` in which each entry is an
            `UnsilenceableRegion`.

    Returns:
        An integer representing a safe line on which to place an error
        suppression comment if it exists. If no safe line exists, this method
        returns -1.
    """
    for region in unsilenceable_regions:
        # It is safe to comment the last line of a multiline string
        if error.line_no == region.end[0] and region.start[0] != region.end[0]:
            continue

        # Error within an UnsilenceableRegion (but not last line of multiline
        # string)
        if region.start[0] <= error.line_no <= region.end[0]:
            return -1

    return error.line_no


def divide_errors(
    unsilenceable_regions: Iterable[UnsilenceableRegion],
    errors: Iterable[MypyError],
) -> tuple[list[MypyError], list[MypyError]]:
    """Divide the MypyErrors into safe and unsafe to silence.

    Args:
        unsilenceable_regions: an iterable whose elements are
            `UnsilenceableRegion`'s in the same file as the errors.
        errors: the errors whose line numbers are to be corrected.

    Returns:
        A 2-tuple whose first entry is a list in which each entry is a
        `MypyError` from `errors` for which type suppression comments can be
        added (with line numbers corrected) and whose second entry is a list
        of each `MypyError` that cannot be silenced.
    """
    line_corrected_errors = []
    unsilenceable_errors = []
    for error in errors:
        end_line = find_safe_end_line(error, unsilenceable_regions)

        if end_line == -1 or error.error_code == "syntax":
            unsilenceable_errors.append(error)
        else:
            line_corrected_errors.append(
                MypyError(
                    error.filename,
                    end_line,
                    error.col_offset,
                    error.message,
                    error.error_code,
                )
            )

    return line_corrected_errors, unsilenceable_errors
