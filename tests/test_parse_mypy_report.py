# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import pathlib
import re
import typing

import pytest

from mypy_upgrade.parsing import MypyError, parse_mypy_report


@pytest.fixture(
    name="report",
    params=(
        "mypy_report_6269340a3.txt",
        "mypy_report_6269340a3_black.txt",
        "mypy_report_35af5282d.txt",
        "mypy_report_35af5282d_black.txt",
    ),
)
def fixture_report(
    shared_datadir: pathlib.Path, request: pytest.FixtureRequest
) -> typing.TextIO:
    file = shared_datadir / "strict_mypy_reports" / request.param
    with pathlib.Path(file).open(encoding="utf-8") as report:
        yield report


class TestParseReport:
    @staticmethod
    @pytest.fixture(name="parsed_errors")
    def fixture_parsed_errors(report: typing.TextIO) -> list[MypyError]:
        parsed_errors = parse_mypy_report(report)
        report.seek(0)
        return parsed_errors

    @staticmethod
    def test_should_return_as_many_entries_as_errors(
        parsed_errors: list[MypyError], report: typing.TextIO
    ):
        summary = report.readlines()[-1]

        match = re.search(r"Found (?P<num_errors>\d+) errors", summary)
        assert match is not None
        num_errors = int(match.group("num_errors"))
        assert num_errors == len(parsed_errors)

    @staticmethod
    def test_should_only_return_mypyerrors(parsed_errors: list[MypyError]):
        assert all(isinstance(e, MypyError) for e in parsed_errors)

    @staticmethod
    def test_should_convert_line_number_to_integer(
        parsed_errors: list[MypyError],
    ):
        assert all(isinstance(e.line_no, int) for e in parsed_errors)

    @staticmethod
    def test_should_strip_whitespace_from_description(
        parsed_errors: list[MypyError],
    ):
        assert (e.description.strip() == e.description for e in parsed_errors)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_filename_first(
        parsed_errors: list[MypyError],
    ):
        filenames = [e.filename for e in parsed_errors]
        assert filenames == sorted(filenames)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_line_number_second(
        parsed_errors: list[MypyError],
    ):
        group_filename = None
        last_line_number = 0
        increasing_within_group = []
        for filename, line_number, *_ in parsed_errors:
            if group_filename == filename:
                increasing_within_group.append(line_number >= last_line_number)
            else:
                group_filename = filename

            last_line_number = line_number

        assert all(increasing_within_group)
