# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Generator
from typing import TextIO

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import parse_mypy_report
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report


@pytest.fixture(name="mypy_upgrade_result", scope="class")
def fixture_mypy_upgrade_result(
    mypy_report_pre: TextIO,
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
    mypy_upgrade_result: MypyUpgradeResult,  # noqa: ARG001
) -> Generator[TextIO, None, None]:
    filename = tmp_path_factory.mktemp("reports") / "mypy_report_post.txt"
    with filename.open("x+") as file:
        subprocess.run(
            [sys.executable, "-m", "mypy", *mypy_args],
            env=os.environ,
            stdout=file,
        )
        yield file


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
        mypy_report_post: TextIO, mypy_upgrade_result: MypyUpgradeResult
    ) -> None:
        errors = parse_mypy_report(mypy_report_post)

        missed_errors = [
            error
            for error in errors
            if error not in mypy_upgrade_result.not_silenced
            and error.error_code != "unused-ignore"
        ]
        assert not missed_errors

    @staticmethod
    def test_should_not_increase_number_of_errors(
        mypy_report_pre: TextIO, mypy_report_post: TextIO
    ) -> None:
        errors_pre = parse_mypy_report(mypy_report_pre)
        errors_post = parse_mypy_report(mypy_report_post)
        assert len(errors_pre) >= len(errors_post)
