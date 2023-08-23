# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
from collections.abc import Generator

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import parse_mypy_report
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report


@pytest.fixture(name="mypy_upgrade_target", scope="class", params=["ase"])
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


@pytest.fixture(
    name="mypy_args", scope="class", params=("strict", "non-strict")
)
def fixture_mypy_args(
    mypy_upgrade_target: str, request: pytest.FixtureRequest
) -> list[str]:
    if request.param == "strict":
        return [
            "--strict",
            "--show-error-codes",
            "--show-absolute-path",
            "-p",
            mypy_upgrade_target,
        ]
    else:
        return [
            "--show-absolute-path",
            "-p",
            mypy_upgrade_target,
        ]


@pytest.fixture(name="python_path", scope="class")
def fixture_python_path(
    install_dir: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[None, None, None]:
    tmp_dir = tmp_path_factory.mktemp("base", numbered=True)
    python_path = tmp_dir.joinpath("__pypackages__").resolve()
    shutil.copytree(install_dir, python_path)
    old_python_path = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = f"{python_path}:{old_python_path}"
    yield None
    os.environ["PYTHONPATH"].replace(f"{python_path}:", "")


@pytest.fixture(name="input_method", params=("pipe", ""))
def fixture_input_method(request: pytest.FixtureRequest) -> str:
    input_method: str = request.param
    return input_method


@pytest.fixture(name="mypy_report_pre", scope="class")
def fixture_mypy_report_pre(
    input_method: str,
    python_path: pathlib.Path,  # noqa: ARG001
    tmp_path_factory: pytest.TempPathFactory,
    mypy_args: list[str],
) -> Generator[pathlib.Path | None, None, None]:
    if input_method == "pipe":
        output = subprocess.check_output(
            [sys.executable, "-m", "mypy", *mypy_args],
            env=os.environ,
            encoding="utf-8",
        )
        sys.argv.append(output)
        yield None
        sys.argv.remove(output)
    else:
        filename = tmp_path_factory.mktemp("reports") / "mypy_report_pre.txt"
        with filename.open("wb") as file:
            subprocess.run(
                [sys.executable, "-m", "mypy", *mypy_args],
                env=os.environ,
                stdout=file,
            )
        yield filename


@pytest.fixture(name="mypy_upgrade_result", scope="class")
def fixture_mypy_upgrade_result(
    mypy_report_pre: pathlib.Path,
    description_style: Literal["full", "none"],
    fix_me: str,
) -> MypyUpgradeResult:
    return silence_errors_in_report(
        report=mypy_report_pre,
        packages=[],
        modules=[],
        files=[],
        description_style=description_style,
        fix_me=fix_me,
    )


@pytest.fixture(name="mypy_report_post", scope="class")
def fixture_mypy_report_post(
    tmp_path_factory: pytest.TempPathFactory,
    mypy_args: list[str],
    mypy_upgrade_results: MypyUpgradeResult,  # noqa: ARG001
) -> pathlib.Path:
    filename = tmp_path_factory.mktemp("reports") / "mypy_report_post.txt"
    with filename.open("wb") as file:
        subprocess.run(
            [sys.executable, "-m", "mypy", *mypy_args],
            env=os.environ,
            stdout=file,
        )
    return filename


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
@pytest.mark.slow
class TestSilenceErrorsInReport:
    @staticmethod
    def test_should_silence_all_silenceable_errors_but_allow_unused_ignore(
        mypy_report_post: pathlib.Path, mypy_upgrade_result: MypyUpgradeResult
    ) -> None:
        with mypy_report_post.open(encoding="utf-8") as file:
            errors = parse_mypy_report(file)

        missed_errors = [
            error
            for error in errors
            if error not in mypy_upgrade_result.not_silenced
            and error.error_code != "unused-ignore"
        ]
        assert not missed_errors

    @staticmethod
    def test_should_not_increase_number_of_errors(
        mypy_report_pre: pathlib.Path, mypy_report_post: pathlib.Path
    ) -> None:
        with mypy_report_pre.open(encoding="utf-8") as file:
            errors_pre = parse_mypy_report(file)
        with mypy_report_post.open(encoding="utf-8") as file:
            errors_post = parse_mypy_report(file)
        assert len(errors_pre) >= len(errors_post)
