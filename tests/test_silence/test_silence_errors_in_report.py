# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import os
import pathlib
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


@pytest.fixture(name="mypy_upgrade_result", scope="class")
def fixture_mypy_upgrade_result(
    report_input_method: Literal["pipe", ""],
    mypy_report_pre: pathlib.Path,
    description_style: Literal["full", "none"],
    fix_me: str,
) -> Generator[MypyUpgradeResult, None, None]:
    if report_input_method == "pipe":
        with mypy_report_pre.open(mode="r", encoding="utf-8") as file:
            start = file.tell()
            report = file.read()
            sys.argv.append(report)
            file.seek(start)
            yield silence_errors_in_report(
                report=None,
                packages=[],
                modules=[],
                files=[],
                description_style=description_style,
                fix_me=fix_me,
            )
            sys.argv.remove(report)
    else:
        yield silence_errors_in_report(
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
    mypy_upgrade_result: MypyUpgradeResult,  # noqa: ARG001
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
