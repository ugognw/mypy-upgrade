import pathlib
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


@pytest.fixture(name="parsed_errors")
def fixture_parsed_errors(report: typing.TextIO) -> list[MypyError]:
    parsed_errors = parse_mypy_report(report)
    report.seek(0)
    return parsed_errors
