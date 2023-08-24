from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
from collections.abc import Generator
from typing import TextIO

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.cli import (
    _create_argument_parser,
)


class TestParseArgs:
    @staticmethod
    @pytest.fixture(
        name="modules",
        params=(
            [],
            ["module"],
            ["package.module"],
            ["module", "package.module"],
        ),
        scope="module",
    )
    def fixture_modules(request: pytest.FixtureRequest) -> list[str]:
        _modules = request.param
        modules = []
        for module in _modules:
            modules.append("-m")
            modules.append(module)

        return modules

    @staticmethod
    @pytest.fixture(
        name="packages",
        params=(
            [],
            ["package"],
            ["package.subpackage"],
            ["package", "package.subpackage"],
        ),
        scope="module",
    )
    def fixture_packages(request: pytest.FixtureRequest) -> list[str]:
        _packages = request.param
        packages = []
        for package in _packages:
            packages.append("-p")
            packages.append(package)

        return packages

    @staticmethod
    @pytest.fixture(name="report", params=([], "report.txt"), scope="module")
    def fixture_report(request: pytest.FixtureRequest) -> list[str]:
        return ["-r", request.param] if request.param else []

    @staticmethod
    @pytest.fixture(
        name="description_style", params=("full", "none"), scope="module"
    )
    def fixture_description_style(request: pytest.FixtureRequest) -> list[str]:
        description_style: str = request.param
        return ["--description-style", description_style]

    @staticmethod
    @pytest.fixture(name="fix_me", params=("FIX ME", ""), scope="module")
    def fixture_fix_me(request: pytest.FixtureRequest) -> list[str]:
        fix_me: str = request.param
        return ["--fix-me", fix_me]

    @staticmethod
    @pytest.fixture(
        name="files",
        params=(
            [],
            ["file.py"],
            ["directory/file.py"],
            ["file.py", "directory/file.py"],
        ),
        scope="module",
    )
    def fixture_files(request: pytest.FixtureRequest) -> list[str]:
        return request.param or []

    @staticmethod
    @pytest.fixture(name="parser", scope="module")
    def fixture_parser() -> argparse.ArgumentParser:
        return _create_argument_parser()

    @staticmethod
    @pytest.fixture(name="args", scope="module")
    def fixture_args(
        modules: list[str],
        packages: list[str],
        report: list[str],
        description_style: list[str],
        fix_me: list[str],
        files: list[str],
        parser: argparse.ArgumentParser,
    ) -> argparse.Namespace:
        return parser.parse_args(
            modules + packages + report + description_style + fix_me + files
        )

    @staticmethod
    def test_should_store_modules(
        args: argparse.Namespace, modules: list[str]
    ) -> None:
        if modules:
            _modules = (
                [m for m in modules if "-" not in m] if modules else None
            )
            assert args.modules == _modules
        else:
            assert args.modules == []

    @staticmethod
    def test_should_store_packages(
        args: argparse.Namespace, packages: list[str]
    ) -> None:
        if packages:
            _packages = (
                [p for p in packages if "-" not in p] if packages else None
            )
            assert args.packages == _packages
        else:
            assert args.packages == []

    @staticmethod
    def test_should_store_files(
        args: argparse.Namespace, files: list[str]
    ) -> None:
        if files:
            _files = [f for f in files if f.endswith(".py")] if files else None
            assert args.files == _files
        else:
            assert args.files == files

    @staticmethod
    def test_should_store_description_style(
        args: argparse.Namespace, description_style: list[str]
    ) -> None:
        assert args.description_style == description_style[1]

    @staticmethod
    def test_should_store_fix_me(
        args: argparse.Namespace, fix_me: list[str]
    ) -> None:
        assert args.fix_me == fix_me[1]

    @staticmethod
    def test_should_store_report(
        args: argparse.Namespace, report: list[str]
    ) -> None:
        if report:
            assert pathlib.Path(report[1]) == args.report
        else:
            assert args.report is None


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
    @pytest.fixture(name="verbosity", scope="class", params=range(3))
    def fixture_verbosity(request: pytest.FixtureRequest) -> int:
        verbosity: int = request.param
        return verbosity

    @staticmethod
    @pytest.fixture(name="args", scope="class")
    def fixture_args(
        mypy_report_pre_filename: pathlib.Path,
        description_style: Literal["full", "none"],
        fix_me: str,
        verbosity: int,
        report_input_method: str,
    ) -> list[str]:
        args: list[str] = []

        args.extend(["-d", description_style])
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
        scope="class",
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
    def test_should_respect_verbosity(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
    ) -> None:
        ...

    @staticmethod
    @pytest.mark.slow
    def test_should_supress_warnings(
        run_mypy_upgrade: subprocess.CompletedProcess[str],
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
