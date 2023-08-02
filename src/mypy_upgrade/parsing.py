# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import re
from typing import NamedTuple, TextIO


class MypyError(NamedTuple):
    filename: str
    line_no: int
    description: str
    error_code: str

    @staticmethod
    def filename_and_line_number(error: MypyError) -> tuple[str, int]:
        return error.filename, error.line_no


def parse_mypy_report(
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
            >> module, line_no, description , error_code= errors[0]
    """
    info = re.compile(
        r"^(?P<filename>[^:]+):(?P<line_no>\d+): error: (?P<description>.+)\s+(\[(?P<error_code>.+)\])?"  # noqa: E501
    )
    errors = []

    for line in report:
        error = info.match(line.strip())
        if error:
            filename, description, error_code = error.group(
                "filename", "description", "error_code"
            )
            line_no = int(error.group("line_no"))
            errors.append(
                MypyError(filename, line_no, description.strip(), error_code)
            )

    return sorted(errors, key=MypyError.filename_and_line_number)


def description_to_type_ignore(description: str) -> tuple[str, ...]:
    type_ignore_re = re.compile(
        r"type\s*:\s*ignore\s*(\[(?P<error_code>[a-z, \-]+)\])?"
    )
    # Extract unused type ignore error codes from error description
    match = type_ignore_re.search(description)
    if match and (error_codes := match.group("error_code")):
        # Separate and trim
        return tuple(code.strip() for code in error_codes.split(","))

    return ()
