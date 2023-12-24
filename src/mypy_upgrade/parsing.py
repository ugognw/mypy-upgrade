"""This module defines the MypyError class and parsing functions."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import logging
import re
from typing import NamedTuple, TextIO

logger = logging.getLogger(__name__)


MISSING_ERROR_CODES = (
    "Not all errors in the mypy type checking report have error "
    "codes. As a result, mypy-upgrade can only suppress these errors "
    "with non-code-specific # type: ignore comments (which will still "
    "raise errors when running mypy with --strict enabled). If you "
    "would like mypy-upgrade to silence errors with code-specific "
    "comments, please run mypy with --show-error-codes enabled. "
    "If you would like to suppress this warning, use the "
    "--allow-no-error-codes flag for mypy-upgrade."
)


class MypyError(NamedTuple):
    """A mypy error

    Attributes:
        filename: a string representing the path containing the error
        line_no: an integer representing the 1-indexed line number where the
            error starts
        col_offset: an integer representing the 0-indexed line number where the
            error starts
        message: the mypy error message
        error_code: the mypy error code
    """

    filename: str
    line_no: int
    col_offset: int | None
    message: str
    error_code: str

    @staticmethod
    def filename_and_line_number(error: MypyError) -> tuple[str, int]:
        return error.filename, error.line_no

    def __str__(self) -> str:
        col_offset = (
            "" if self.col_offset is not None else f":{self.col_offset}"
        )
        return f"{self.filename}:{self.line_no}{col_offset}:{self.error_code}"


def parse_mypy_report(
    *,
    report: TextIO,
) -> list[MypyError]:
    """Parse a mypy error report from stdin.

    Args:
        report: a text stream from which to read the mypy typing report
    Returns:
        A sorted list of MypyErrors. Elements are sorted by their filename
        and line_no attributes.

        Example::

            >> report = pathlib.Path('mypy_report.txt').open(encoding='utf-8')
            >> errors = parse_report(report)
            >> module, col_offset, line_no, message , error_code= errors[0]
    """
    start = report.tell()
    info = re.compile(
        r"^(?P<filename>[^:]+):(?P<line_no>\d+)(:(?P<col_offset>\d+))?"
        r"(:\d+:\d+)?: error: (?P<message>.+)\s+(\[(?P<error_code>.+)\])?"
    )
    errors = []

    for line in report:
        error = info.match(line.strip())
        if error:
            error_code = error.group("error_code") or ""
            filename, message = error.group("filename", "message")
            line_no = int(error.group("line_no"))
            if error.group("col_offset"):
                col_offset = int(error.group("col_offset"))
            else:
                col_offset = None

            errors.append(
                MypyError(
                    filename,
                    line_no,
                    col_offset,
                    message.strip(),
                    error_code,
                )
            )
    report.seek(start)
    if any(not error.error_code for error in errors):
        logger.warning(MISSING_ERROR_CODES)
    return sorted(errors, key=MypyError.filename_and_line_number)


def string_to_error_codes(*, string: str) -> tuple[str, ...]:
    """Return the error codes in a string containin the phrase "type: ignore"

    Args:
        string: a string containing "type: ignore"

    Returns:
        A tuple of strings, each of which is a mypy error code. If no error
        codes exist within the "string" parameter, return an empty tuple.

        If multiple "type: ignore" phrases exist, the error codes
        corresponding to phrase with more error codes is returned.

    Example::
        >>> string = (
        ... '"type: ignore" comment without error code (consider '
        ... '"type: ignore[operator, type-var]" instead)'
        ... )
        >>> string_to_error_codes(string=string)
        ("operator", "type-var")
    """
    type_ignore_re = re.compile(
        r"type\s*:\s*ignore\s*(?:\[(?P<error_code>[a-z, \-]+)\])?"
    )
    # Extract unused type ignore error codes from error description
    code_match = type_ignore_re.findall(string)
    type_ignore_re.search(string)
    if code_match:
        error_codes = max(code_match)
        if error_codes:
            # Separate and trim
            return tuple({code.strip() for code in error_codes.split(",")})

    return ()
