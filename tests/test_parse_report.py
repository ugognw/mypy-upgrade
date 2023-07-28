import pathlib
import typing

import pytest

from mypy_upgrade.__main__ import parse_report


@pytest.fixture(name="report", params=["mypy_results.txt", "relative_mypy_results.txt"])
def fixture_report(shared_datadir: pathlib.Path, request: pytest.FixtureRequest) -> typing.IO:
    marker = request.node.get_closest_marker("results_file")
    if marker is not None:
        file = shared_datadir / marker.args[0]
    else:
        file = shared_datadir / request.param

    with open(file) as report:
        yield report


class TestParseReport:
    @staticmethod
    def test_should_return_as_many_entries_as_errors(report: typing.IO):
        lines = list(report)
        num_lines = 0
        for line in lines:
            if ": error:" in line:
                num_lines += 1

        _ = report.seek(0)
        errors = parse_report(report)

        assert num_lines == len(errors)

    @staticmethod
    def test_should_create_four_entry_tuples(report: typing.IO):
        errors = parse_report(report)
        check = []
        for error in errors:
            check.append(len(error) == 4)

        assert False not in check

    @staticmethod
    @pytest.mark.results_file("relative_mypy_results.txt")
    def test_should_create_existing_paths(report: typing.IO):
        errors = parse_report(report)
        check = []
        for module, *_ in errors:
            check.append(pathlib.Path(module).exists())

        assert False not in check
