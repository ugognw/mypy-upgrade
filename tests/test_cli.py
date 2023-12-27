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

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.silence import MypyUpgradeResult

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.cli import (
    _process_options,
    summarize_results,
)


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
    @pytest.fixture(name="verbosity", params=range(3))
    def fixture_verbosity(request: pytest.FixtureRequest) -> int:
        verbosity: int = request.param
        return verbosity

    @staticmethod
    @pytest.fixture(name="colours", params=[False])
    def fixture_colours(request: pytest.FixtureRequest) -> int:
        colours: int = request.param
        return colours

    @staticmethod
    @pytest.fixture(name="suppress_warnings", params=[False])
    def fixture_suppress_warnings(request: pytest.FixtureRequest) -> int:
        suppress_warnings: int = request.param
        return suppress_warnings

    @staticmethod
    @pytest.fixture(name="summarize", params=[False])
    def fixture_summarize(request: pytest.FixtureRequest) -> int:
        summarize: int = request.param
        return summarize

    @staticmethod
    @pytest.fixture(name="args")
    def fixture_args(
        *,
        mypy_report_pre_filename: pathlib.Path,
        description_style: Literal["full", "none"],
        fix_me: str,
        verbosity: int,
        report_input_method: str,
        colours: bool,
        suppress_warnings: bool,
        summarize: bool,
    ) -> list[str]:
        args: list[str] = []

        args.extend(["-d", description_style])
        if colours:
            args.append("--colours")
        if suppress_warnings:
            args.append("--suppress-warnings")
        if summarize:
            args.append("--summarize")
        if fix_me.strip():
            args.extend(["--fix-me", fix_me])
        else:
            args.extend(["--fix-me", " "])

        if verbosity == 1:
            args.append("-v")
        elif verbosity == 2:
            args.append("-vv")

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
    @pytest.mark.parametrize("colours", [True])
    def test_should_run_with_colours(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
        colours: bool,  # noqa: FBT001
    ) -> None:
        ...

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("supress_warnings", [True])
    def test_should_supress_warnings(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
        supress_warnings: bool,  # noqa: FBT001
    ) -> None:
        ...

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("summarize", [True])
    def test_should_summarize(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
        summarize: bool,  # noqa: FBT001
    ) -> None:
        ...

    @staticmethod
    @pytest.mark.parametrize(
        "executable",
        [["mypy-upgrade"], [sys.executable, "-m", "mypy_upgrade"]],
    )
    def test_should_print_version(
        args: list[str],
        executable: list[str],
        report_input_method: str,
        tmp_path: pathlib.Path,
        coverage_py_subprocess_setup: None,  # noqa: ARG004
    ) -> None:
        if report_input_method == "pipe":
            mypy_report_pre = tmp_path.joinpath("report.txt")
            mypy_report_pre.touch()
            with mypy_report_pre.open(mode="r", encoding="utf-8") as report:
                process = subprocess.run(  # noqa: PLW1510
                    [*executable, *args, "-V"],
                    capture_output=True,
                    encoding="utf-8",
                    stdin=report,
                )
        else:
            process = subprocess.run(  # noqa: PLW1510
                [*executable, *args, "-V"],
                capture_output=True,
                encoding="utf-8",
            )

        assert __version__ in process.stdout
