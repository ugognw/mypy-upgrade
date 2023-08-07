from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

import pytest

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.cli import _create_argument_parser, main, mypy_upgrade


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


@pytest.mark.skip(
    reason="only intended to be run on git ref 6269340a3 of branch master"
)
class TestMypyUpgrade6269340a3:
    @staticmethod
    @pytest.mark.functional1
    def test_functional1(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "with_columns",
            "6269340a3",
            "baseline_report_7c2def18.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules

    @staticmethod
    @pytest.mark.functional2
    def test_functional2(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "with_columns",
            "6269340a3",
            "second_report_96c979674.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules

    @staticmethod
    @pytest.mark.functional3
    def test_functional3(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "with_columns",
            "6269340a3",
            "third_report_ba79c42c7.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules


@pytest.mark.skip(
    reason="only intended to be run on git ref 35af5282d of branch master"
)
class TestMypyUpgrade35af5282d:
    @staticmethod
    @pytest.mark.functional1
    def test_functional1(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "35af5282d",
            "with_columns",
            "baseline_report_47a422c16.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules

    @staticmethod
    @pytest.mark.functional2
    def test_functional2(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "with_columns",
            "35af5282d",
            "second_report_6f100101a.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules

    @staticmethod
    @pytest.mark.functional3
    def test_functional3(
        shared_datadir: pathlib.Path,
    ) -> None:
        report = shared_datadir.joinpath(
            "mypy_reports",
            "with_columns",
            "35af5282d",
            "third_report_ba79c42c7.txt",
        )
        errors, modules = mypy_upgrade(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="none",
            fix_me="FIX ME",
        )
        assert (
            len(errors) == len(report.open(encoding="utf-8").readlines()) - 1
        )
        assert modules


class TestMain:
    @staticmethod
    @pytest.mark.skip(reason="need to refactor functional test")
    def test(
        shared_datadir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        report = str(shared_datadir / "mypy_fix-1267.txt")

        with monkeypatch.context() as mp:
            os.chdir("/Users/ugo/Projects/nwt/ase")
            mp.syspath_prepend("/Users/ugo/Projects/nwt/ase")
            mp.setattr(
                sys,
                "argv",
                [sys.argv[0], "--package", "ase", "--report", report],
            )
            main()

    @staticmethod
    def test_should_print_version() -> None:
        output = subprocess.check_output(
            ["mypy-upgrade", "-V"], encoding="utf-8"  # noqa: S603, S607
        )
        assert __version__ in output
