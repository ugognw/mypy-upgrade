import argparse
import pathlib

import pytest

from mypy_upgrade.cli import _create_argument_parser


@pytest.fixture(
    name="modules",
    params=([], ["module"], ["package.module"], ["module", "package.module"]),
    scope="class",
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
    scope="class",
)
def fixture_packages(request: pytest.FixtureRequest) -> list[str]:
    _packages = request.param
    packages = []
    for package in _packages:
        packages.append("-p")
        packages.append(package)

    return packages


@pytest.fixture(name="report", params=([], "report.txt"), scope="class")
def fixture_report(request: pytest.FixtureRequest) -> list[str]:
    if report := request.param:
        return ["-r", report]
    return []


@pytest.fixture(
    name="suffix", params=("--with-descriptions", None), scope="class"
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
    scope="class",
)
def fixture_files(request: pytest.FixtureRequest) -> list[str]:
    return request.param or []


@pytest.fixture(name="parser", scope="class")
def fixture_parser() -> argparse.ArgumentParser:
    return _create_argument_parser()


@pytest.fixture(name="args", scope="class")
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
    ):
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
    ):
        if packages:
            _packages = (
                [p for p in packages if "-" not in p] if packages else None
            )
            assert args.packages == _packages
        else:
            assert args.packages == []

    @staticmethod
    def test_should_store_files(args: argparse.Namespace, files: list[str]):
        if files:
            _files = [f for f in files if f.endswith(".py")] if files else None
            assert args.files == _files
        else:
            assert args.files == files

    @staticmethod
    def test_should_store_report(args: argparse.Namespace, report: list[str]):
        if report:
            assert pathlib.Path(report[1]) == args.report
        else:
            assert args.report is None

    @staticmethod
    def test_should_store_suffix(args: argparse.Namespace, suffix: str | None):
        if suffix == "--with-descriptions":
            assert args.suffix == "description"
        else:
            assert args.suffix == suffix
