from __future__ import annotations

import contextlib
import os
import pathlib
import shutil
import subprocess
import sys
from collections.abc import Generator
from io import TextIOWrapper
from typing import TextIO

import pytest

from mypy_upgrade.cli import (
    _process_options,
    summarize_results,
)
from mypy_upgrade.parsing import MypyError
from mypy_upgrade.silence import MypyUpgradeResult


class TestProcessOptions:
    @staticmethod
    def test_should_read_from_defaults() -> None:
        assert _process_options()


class TestSummarizeResults:
    @staticmethod
    @pytest.fixture(name="results")
    def fixture_results() -> MypyUpgradeResult:
        results = MypyUpgradeResult(
            silenced=(
                MypyError("file1.py", 1, 1, "message", "error-code"),
                MypyError("file1.py", 2, 2, "message", "error-code"),
            ),
            not_silenced=(
                MypyError("file2.py", 1, 1, "message", "error-code"),
            ),
            ignored=(MypyError("file3.py", 1, 1, "message", "error-code"),),
        )
        return results

    @staticmethod
    @pytest.fixture(name="summarized_results")
    def fixture_summarized_results(
        results: MypyUpgradeResult, verbosity: int, tmp_path: pathlib.Path
    ) -> Generator[TextIOWrapper, None, None]:
        output = tmp_path.joinpath("output.txt")
        with output.open(
            mode="w", encoding="utf-8"
        ) as file, contextlib.redirect_stdout(file):
            summarize_results(results=results, verbosity=verbosity)

        with output.open(mode="r", encoding="utf-8") as file:
            yield file

    @staticmethod
    @pytest.mark.parametrize("verbosity", [0])
    def test_should_print_simple_summary_with_no_verbosity(
        summarized_results: TextIO,
    ) -> None:
        start = summarized_results.tell()
        summary = summarized_results.read()
        summarized_results.seek(start)
        assert "SUMMARY" in summary

    @staticmethod
    @pytest.mark.parametrize("verbosity", [1])
    def test_should_print_long_summary_with_verbosity(
        summarized_results: TextIO,
    ) -> None:
        start = summarized_results.tell()
        summary = summarized_results.read()
        summarized_results.seek(start)
        assert "SILENCED" in summary


@pytest.mark.skipif(
    "CI" not in os.environ,
    reason="CI-only tests",
)
@pytest.mark.skipif(
    "MYPY_UPGRADE_TARGET" not in os.environ,
    reason="no target specified for mypy-upgrade",
)
@pytest.mark.skipif(
    "MYPY_UPGRADE_TARGET_INSTALL_DIR" not in os.environ,
    reason="no install directory specified for mypy-upgrade",
)
@pytest.mark.cli
class TestCLI:
    @staticmethod
    @pytest.fixture(name="summarize", params=[False, True])
    def fixture_summarize(request: pytest.FixtureRequest) -> int:
        summarize: int = request.param
        return summarize

    @staticmethod
    @pytest.fixture(name="args")
    def fixture_args(
        *,
        summarize: bool,
        report_input_method: str,
        mypy_report_pre_filename: pathlib.Path,
    ) -> list[str]:
        args: list[str] = ["--dry-run"]

        if summarize:
            args.append("--summarize")

        if report_input_method != "pipe":
            args.extend(["-r", str(mypy_report_pre_filename)])

        return args

    @staticmethod
    @pytest.fixture(
        name="run_mypy_upgrade",
        params=(["mypy-upgrade"], [sys.executable, "-m", "mypy_upgrade"]),
    )
    def fixture_run_mypy_upgrade(
        request: pytest.FixtureRequest,
        args: list[str],
        report_input_method: str,
        mypy_report_pre: TextIO,
        python_path: pathlib.Path,
        install_dir: pathlib.Path,
        coverage_py_subprocess_setup: None,  # noqa: ARG004
    ) -> Generator[subprocess.CompletedProcess[str], None, None]:
        executable: list[str] = request.param
        if report_input_method == "pipe":
            yield subprocess.run(  # noqa: PLW1510
                [*executable, *args],
                capture_output=True,
                encoding="utf-8",
                stdin=mypy_report_pre,
            )
        else:
            yield subprocess.run(  # noqa: PLW1510
                [*executable, *args], capture_output=True, encoding="utf-8"
            )
        if sys.version_info < (3, 8):
            shutil.rmtree(python_path)
            shutil.copytree(install_dir, python_path)
        else:
            shutil.copytree(install_dir, python_path, dirs_exist_ok=True)

    @staticmethod
    @pytest.mark.slow
    def test_should_exit_with_zero(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
    ) -> None:
        assert run_mypy_upgrade.returncode == 0

    @staticmethod
    @pytest.mark.slow
    def test_should_respect_summary_configuration(
        *,
        run_mypy_upgrade: subprocess.CompletedProcess[str],
        summarize: bool,
    ) -> None:
        assert ("SUMMARY" in run_mypy_upgrade.stdout) == summarize
