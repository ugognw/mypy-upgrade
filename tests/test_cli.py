from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Generator

import pytest

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.cli import (
    MypyUpgradeResult,
    _create_argument_parser,
    mypy_upgrade,
)
from mypy_upgrade.parsing import parse_mypy_report


@pytest.fixture(
    name="modules",
    params=([], ["module"], ["package.module"], ["module", "package.module"]),
    scope="module",
)
def fixture_modules(request: pytest.FixtureRequest) -> list[str]:
    _modules = request.param
    modules = []
    for module in _modules:
        modules.append("-m")
        modules.append(module)

    return modules


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


@pytest.fixture(name="report", params=([], "report.txt"), scope="module")
def fixture_report(request: pytest.FixtureRequest) -> list[str]:
    return ["-r", request.param] if request.param else []


@pytest.fixture(
    name="description_style", params=("full", "none"), scope="module"
)
def fixture_description_style(request: pytest.FixtureRequest) -> list[str]:
    description_style: str = request.param
    return ["--description-style", description_style]


@pytest.fixture(name="fix_me", params=("FIX ME", ""), scope="module")
def fixture_fix_me(request: pytest.FixtureRequest) -> list[str]:
    fix_me: str = request.param
    return ["--fix-me", fix_me]


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


@pytest.fixture(name="parser", scope="module")
def fixture_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = _create_argument_parser()
    return parser


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


class TestParseArgs:
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


@pytest.fixture(name="mypy_args", scope="session")
def fixture_mypy_args() -> list[str]:
    return [
        "--strict",
        "--show-error-codes",
        "--show-absolute-path",
        "--show-column-numbers",
        "-p",
        os.environ["MYPY_UPGRADE_TARGET"],
    ]


@pytest.fixture(name="python_path", scope="class")
def fixture_python_path(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    tmp_dir = tmp_path_factory.mktemp("base", numbered=True)
    python_path = tmp_dir.joinpath("__pypackages__")
    shutil.copytree(os.environ["MYPY_UPGRADE_TARGET_INSTALL_DIR"], python_path)
    return python_path


@pytest.fixture(name="mypy_report_pre", scope="class")
def fixture_mypy_report_pre(
    python_path: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    mypy_args: list[str],
) -> Generator[pathlib.Path, None, None]:
    filename = tmp_path_factory.mktemp("reports") / "mypy_report_pre.txt"
    with filename.open("w") as file:
        from mypy.main import main

        sys.path.insert(0, str(python_path))
        main(args=mypy_args, stdout=file)
    yield filename
    sys.path.remove(str(python_path))


@pytest.mark.skip
@pytest.mark.skipif(
    "CI" not in os.environ,
    reason="CI-only tests",
)
@pytest.mark.skipif(
    "MYPY_UPGRADE_TARGET" not in os.environ,
    reason="no target specified for mypy-upgrade",
)
@pytest.mark.slow
@pytest.mark.mypy_upgrade
class TestMypyUpgrade:
    @pytest.fixture(name="mypy_upgrade_results", scope="class")
    @staticmethod
    def fixture_mypy_upgrade_results(
        mypy_report_pre: pathlib.Path,
    ) -> MypyUpgradeResult:
        return mypy_upgrade(
            report=mypy_report_pre,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )

    @pytest.fixture(name="mypy_report_post", scope="class")
    @staticmethod
    def fixture_mypy_report_post(
        tmp_path_factory: pytest.TempPathFactory,
        mypy_args: list[str],
        mypy_upgrade_results: MypyUpgradeResult,  # noqa: ARG004
    ) -> pathlib.Path:
        filename = tmp_path_factory.mktemp("reports") / "mypy_report_post.txt"
        from mypy.main import main

        with filename.open(mode="w", encoding="utf-8") as file:
            main(args=mypy_args, stdout=file)
        return filename

    @staticmethod
    def test_should_silence_all_silenceable_errors(
        mypy_report_post: pathlib.Path, mypy_upgrade_results: MypyUpgradeResult
    ) -> None:
        with mypy_report_post.open(encoding="utf-8") as file:
            errors = parse_mypy_report(file)
        assert len(mypy_upgrade_results.not_silenced) == len(errors)

    @staticmethod
    def test_should_not_increase_number_of_errors(
        mypy_report_pre: pathlib.Path, mypy_report_post: pathlib.Path
    ) -> None:
        with mypy_report_pre.open(encoding="utf-8") as file:
            errors_pre = parse_mypy_report(file)
        with mypy_report_post.open(encoding="utf-8") as file:
            errors_post = parse_mypy_report(file)
        assert len(errors_pre) >= len(errors_post)


@pytest.mark.cli
class TestCLI:
    @staticmethod
    @pytest.mark.skip
    @pytest.mark.skipif(
        "CI" not in os.environ or "MYPY_UPGRADE_TARGET" not in os.environ,
        reason="CI-only tests or no target specified for mypy-upgrade",
    )
    @pytest.mark.slow
    def test_should_exit_with_zero(mypy_report_pre: pathlib.Path) -> None:
        process = subprocess.run(
            ["mypy-upgrade", "--r", str(mypy_report_pre)]  # noqa: S607
        )
        assert process.returncode == 0

    @staticmethod
    def test_should_print_unable_to_find_report_if_report_does_not_exist() -> (
        None
    ):
        output = subprocess.check_output(
            ["mypy-upgrade", "--r", ".non_existent_report.fake"],  # noqa: S607
        )
        assert b"Aborting: Unable to find report" in output

    @staticmethod
    def test_should_print_version() -> None:
        output = subprocess.check_output(
            ["mypy-upgrade", "-V"], encoding="utf-8"  # noqa: S607
        )
        assert __version__ in output
