import pathlib
import typing

import pytest

from mypy_upgrade.parsing import MypyError, parse_mypy_report


@pytest.fixture(
    name="report",
    params=(
        "35af5282d/baseline_report_47a422c16.txt",
        "35af5282d/second_report_6f100101a.txt",
        "6269340a3/baseline_report_7c2def18.txt",
        "6269340a3/second_report_96c979674.txt",
        "6269340a3/third_report_ba79c42c7.txt",
    ),
)
def fixture_report(
    shared_datadir: pathlib.Path, request: pytest.FixtureRequest
) -> typing.TextIO:
    file = shared_datadir / "mypy_reports" / request.param
    with pathlib.Path(file).open(encoding="utf-8") as report:
        yield report


@pytest.fixture(name="parsed_errors")
def fixture_parsed_errors(report: typing.TextIO) -> list[MypyError]:
    parsed_errors = parse_mypy_report(report)
    report.seek(0)
    return parsed_errors
