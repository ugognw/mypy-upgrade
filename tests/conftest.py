from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import typing
from collections.abc import Generator
from typing import TextIO

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import MypyError, parse_mypy_report


@pytest.fixture(
    name="report",
    params=(
        "35af5282d/with_columns/baseline_report_47a422c16.txt",
        "35af5282d/without_columns/baseline_report_47a422c16.txt",
        "stdlib_report.txt",
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


@pytest.fixture(name="mypy_upgrade_target", scope="session", params=["ase"])
def fixture_mypy_upgrade_target(request: pytest.FixtureRequest) -> str:
    if "CI" in os.environ:
        return os.environ["MYPY_UPGRADE_TARGET"]
    target: str = request.param
    return target


@pytest.fixture(name="install_dir", scope="session")
def fixture_install_dir() -> str:
    if "CI" in os.environ:
        return os.environ["MYPY_UPGRADE_TARGET_INSTALL_DIR"]
    return "/Users/ugo/Projects/nwt/mypy-upgrade/downloads"


@pytest.fixture(name="mypy_config_file", scope="session")
def fixture_mypy_config_file(tmp_path_factory: pytest.TempPathFactory) -> str:
    mypy_config_file = tmp_path_factory.getbasetemp().joinpath("mypy.ini")
    with mypy_config_file.open(mode="x", encoding="utf-8") as file:
        file.write("[mypy]")
    return str(mypy_config_file)


@pytest.fixture(
    name="mypy_args", scope="session", params=("strict", "non-strict")
)
def fixture_mypy_args(
    mypy_config_file: str,
    mypy_upgrade_target: str,
    request: pytest.FixtureRequest,
) -> list[str]:
    if request.param == "strict":
        return [
            "--strict",
            "--config-file",
            mypy_config_file,
            "--show-error-codes",
            "--show-absolute-path",
            "-p",
            mypy_upgrade_target,
        ]
    else:
        return [
            "--config-file",
            mypy_config_file,
            "--show-absolute-path",
            "--hide-error-codes",
            "-p",
            mypy_upgrade_target,
        ]


@pytest.fixture(name="python_path", scope="session")
def fixture_python_path(
    install_dir: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[pathlib.Path, None, None]:
    tmp_dir = tmp_path_factory.mktemp("base", numbered=True)
    python_path = tmp_dir.joinpath("__pypackages__").resolve()
    shutil.copytree(install_dir, python_path)
    old_python_path = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = f"{python_path}:{old_python_path}"
    yield python_path
    os.environ["PYTHONPATH"].replace(f"{python_path}:", "")


@pytest.fixture(
    name="report_input_method", scope="session", params=("pipe", "")
)
def fixture_report_input_method(
    request: pytest.FixtureRequest,
) -> Literal["pipe", ""]:
    report_input_method: Literal["pipe", ""] = request.param
    return report_input_method


@pytest.fixture(
    name="description_style", scope="session", params=("full", "none")
)
def fixture_description_style(
    request: pytest.FixtureRequest,
) -> Literal["full", "none"]:
    description_style: Literal["full", "none"] = request.param
    return description_style


@pytest.fixture(name="fix_me", scope="session", params=("FIX ME", ""))
def fixture_fix_me(request: pytest.FixtureRequest) -> str:
    fix_me: str = request.param
    return fix_me


@pytest.fixture(name="mypy_report_pre_filename", scope="session")
def fixture_mypy_report_pre_filename(
    tmp_path_factory: pytest.TempPathFactory,
    mypy_args: list[str],
) -> pathlib.Path:
    if "--strict" in mypy_args:
        return tmp_path_factory.mktemp("reports").joinpath(
            "mypy_report_pre_strict.txt"
        )
    return tmp_path_factory.mktemp("reports").joinpath("mypy_report_pre.txt")


@pytest.fixture(name="mypy_report_pre", scope="session")
def fixture_mypy_report_pre(
    python_path: pathlib.Path,  # noqa: ARG001
    mypy_report_pre_filename: pathlib.Path,
    mypy_args: list[str],
) -> Generator[TextIO, None, None]:
    with mypy_report_pre_filename.open("x+") as file:
        subprocess.run(  # noqa: PLW1510
            [
                sys.executable,
                "-m",
                "mypy",
                "--install-types",
                "--non-interactive",
                *mypy_args,
            ],
            env=os.environ,
            encoding="utf-8",
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(  # noqa: PLW1510
            [sys.executable, "-m", "mypy", *mypy_args],
            env=os.environ,
            encoding="utf-8",
            stdout=file,
        )
        file.seek(0)
        yield file
