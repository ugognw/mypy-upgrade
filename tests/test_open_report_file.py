import pathlib
import re
import sys

from mypy_upgrade.__main__ import open_report_file


class TestFileInput:
    @staticmethod
    def test_should_open_text_file(shared_datadir: pathlib.Path):
        file = shared_datadir / "mypy_results.txt"
        with open_report_file(file) as report:
            lines = report.readlines()

        assert re.search(r"checked \d+ source files", lines[-1])

    @staticmethod
    def test_should_open_stdin_file(shared_datadir: pathlib.Path):
        file = shared_datadir / "mypy_results.txt"
        with open(file) as report:
            text = report.read()

        del sys.argv[1:]
        sys.argv.append(text)

        with open_report_file(None) as report:
            lines = report.readlines()

        assert re.search(r"checked \d+ source files", lines[-1])

    @staticmethod
    def test_should_open_mypy_result():
        del sys.argv[1:]
        with open_report_file(None) as report:
            lines = report.readlines()

        assert re.search(r"checked \d+ source files", lines[-1])
