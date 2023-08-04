from __future__ import annotations

import argparse
import os
import pathlib
import sys

import pytest

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
    name="suffix", params=("--with-descriptions", None), scope="module"
)
def fixture_suffix(request: pytest.FixtureRequest) -> str:
    return request.param


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
    return _create_argument_parser()


@pytest.fixture(name="args", scope="module")
def fixture_args(
    modules: list[str],
    packages: list[str],
    report: list[str],
    suffix: str,
    files: list[str],
    parser: argparse.ArgumentParser,
) -> argparse.Namespace:
    if suffix is None:
        return parser.parse_args(modules + packages + report + files)

    return parser.parse_args(modules + packages + report + [suffix] + files)


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
    def test_should_store_report(
        args: argparse.Namespace, report: list[str]
    ) -> None:
        if report:
            assert pathlib.Path(report[1]) == args.report
        else:
            assert args.report is None

    @staticmethod
    def test_should_store_suffix(
        args: argparse.Namespace, suffix: str | None
    ) -> None:
        if suffix == "--with-descriptions":
            assert args.suffix == "description"
        else:
            assert args.suffix == suffix


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
            "mypy_reports", "6269340a3", "baseline_report_7c2def18.txt"
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
            "mypy_reports", "6269340a3", "second_report_96c979674.txt"
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
            "mypy_reports", "6269340a3", "third_report_ba79c42c7.txt"
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
            "mypy_reports", "35af5282d", "baseline_report_47a422c16.txt"
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
            "35af5282d",
            "second_report_6f100101a.txt",
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
            "mypy_reports", "35af5282d", "third_report_ba79c42c7.txt"
        )
        errors, modules = mypy_upgrade(
            report,
            [],
            [],
            [],
            None,
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
