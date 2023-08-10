from __future__ import annotations

import pathlib
import typing
from collections.abc import Generator

import pytest

from mypy_upgrade.parsing import MypyError, parse_mypy_report


@pytest.fixture(
    name="report",
    params=(
        "35af5282d/with_columns/baseline_report_47a422c16.txt",
        "35af5282d/without_columns/baseline_report_47a422c16.txt",
    ),
)
def fixture_report(
    shared_datadir: pathlib.Path, request: pytest.FixtureRequest
) -> Generator[typing.TextIO, None, None]:
    file = shared_datadir / "mypy_reports" / request.param
    with pathlib.Path(file).open(encoding="utf-8") as report:
        yield report


@pytest.fixture(name="parsed_errors")
def fixture_parsed_errors(report: typing.TextIO) -> list[MypyError]:
    parsed_errors: list[MypyError] = parse_mypy_report(report)
    report.seek(0)
    return parsed_errors
