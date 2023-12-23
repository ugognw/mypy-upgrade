# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import logging
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

from mypy_upgrade.parsing import parse_mypy_report
from mypy_upgrade.silence import (
    TRY_SHOW_ABSOLUTE_PATH,
    MypyUpgradeResult,
    silence_errors_in_report,
)


@pytest.fixture(name="log_level")
def fixture_log_level() -> int:
    level = logging.DEBUG

    return level


@pytest.fixture(name="configure_logging")
def fixture_configure_logging(  # noqa: PT004
    log_level: int, log_file: pathlib.Path
) -> None:
    root_logger = logging.getLogger()
    fh = logging.FileHandler(filename=log_file)
    fh.setLevel(level=log_level)
    root_logger.addHandler(fh)


@pytest.fixture(name="dry_run", scope="class")
def fixture_dry_run() -> bool:
    dry_run = False

    return dry_run


@pytest.fixture(name="codes_to_silence", scope="class")
def fixture_codes_to_silence() -> list[str] | None:
    only_codes_to_silence: list[str] | None = None
    return only_codes_to_silence


@pytest.fixture(name="mypy_upgrade_result", scope="class")
def fixture_mypy_upgrade_result(
    *,
    mypy_report_pre: TextIO,
    description_style: Literal["full", "none"],
    fix_me: str,
    dry_run: bool,
    codes_to_silence: list[str],
    python_path: pathlib.Path,
    install_dir: pathlib.Path,
) -> Generator[MypyUpgradeResult, None, None]:
    yield silence_errors_in_report(
        report=mypy_report_pre,
        packages=[],
        modules=[],
        files=[],
        description_style=description_style,
        fix_me=fix_me,
        dry_run=dry_run,
        codes_to_silence=codes_to_silence,
    )
    if sys.version_info < (3, 8):
        shutil.rmtree(python_path)
        shutil.copytree(install_dir, python_path)
    else:
        shutil.copytree(install_dir, python_path, dirs_exist_ok=True)


@pytest.fixture(name="mypy_report_post", scope="class")
def fixture_mypy_report_post(
    tmp_path_factory: pytest.TempPathFactory,
    mypy_args: list[str],
    mypy_upgrade_result: MypyUpgradeResult,  # noqa: ARG001
) -> Generator[TextIO, None, None]:
    filename = tmp_path_factory.mktemp("reports") / "mypy_report_post.txt"
    with filename.open("x+") as file:
        subprocess.run(  # noqa: PLW1510
            [sys.executable, "-m", "mypy", *mypy_args],
            env=os.environ,
            stdout=file,
        )
        file.seek(0)
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
@pytest.mark.api
@pytest.mark.slow
class TestSilenceErrorsInReport:
    @staticmethod
    def test_should_silence_all_silenceable_errors_but_unused_ignore_errors(
        mypy_report_post: TextIO, mypy_upgrade_result: MypyUpgradeResult
    ) -> None:
        errors = parse_mypy_report(report=mypy_report_post)

        missed_errors = [
            error
            for error in errors
            if error not in mypy_upgrade_result.not_silenced
            and error.error_code != "unused-ignore"
        ]
        assert not missed_errors

    @staticmethod
    @pytest.mark.parametrize("codes_to_silence", [[], ["arg-type"]])
    def test_should_only_silence_errors_in_errors_to_silence(
        mypy_upgrade_result: MypyUpgradeResult,
        codes_to_silence: list[str],
    ) -> None:
        assert all(
            error in codes_to_silence for error in mypy_upgrade_result.silenced
        )

    @staticmethod
    def test_should_not_increase_number_of_errors(
        mypy_report_pre: TextIO, mypy_report_post: TextIO
    ) -> None:
        errors_pre = parse_mypy_report(report=mypy_report_pre)
        errors_post = parse_mypy_report(report=mypy_report_post)
        assert len(errors_pre) >= len(errors_post)

    @staticmethod
    def test_should_only_silence_selected_errors() -> None:
        assert True

    @staticmethod
    def test_should_silence_all_errors_if_no_errors_specified() -> None:
        assert True


@pytest.mark.usefixtures("configure_logging")
class TestCatchFileNotFoundError:
    @staticmethod
    @pytest.fixture(name="report")
    def fixture_report() -> TextIO:
        lines = [
            "/nonexistent/path/to/nonexistent/module.py:1:1: error: "
            "Function is missing a return type annotation  [no-untyped-def]",
            "Found 1 error in 1 file (checked 1 source file)",
        ]
        return io.StringIO("\n".join(lines))

    @staticmethod
    def test_should_catch_file_not_found_error(
        report: TextIO, log_file: pathlib.Path
    ) -> None:
        result = silence_errors_in_report(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="full",
            fix_me="",
            dry_run=False,
        )
        filename = result.not_silenced[0].filename
        message = TRY_SHOW_ABSOLUTE_PATH.replace("{filename}", filename)
        with log_file.open(mode="r", encoding="utf-8") as file:
            assert any(message in msg for msg in file.readlines())


@pytest.mark.usefixtures("configure_logging")
class TestCatchTokenError:
    @staticmethod
    @pytest.fixture(name="source_file", params=("x +\\\n", "(", "'''"))
    def fixture_source_file(
        request: pytest.FixtureRequest, tmp_path: pathlib.Path
    ) -> pathlib.Path:
        source_file = tmp_path.joinpath("module.py")
        code: str = request.param
        with source_file.open(mode="x", encoding="utf=8") as file:
            file.write(code)
        return source_file

    @staticmethod
    @pytest.fixture(name="report")
    def fixture_report(source_file: pathlib.Path) -> TextIO:
        lines = [
            f"{source_file!s}:1:1: error: "
            "Function is missing a return type annotation  [no-untyped-def]",
            "Found 1 error in 1 file (checked 1 source file)",
        ]
        return io.StringIO("\n".join(lines))

    @staticmethod
    def test_should_catch_token_error(
        report: TextIO, log_file: pathlib.Path
    ) -> None:
        result = silence_errors_in_report(
            report=report,
            packages=[],
            modules=[],
            files=[],
            description_style="full",
            fix_me="",
            dry_run=False,
        )
        filename = result.not_silenced[0].filename
        message = f"Unable to tokenize file: {filename}"
        with log_file.open(mode="r", encoding="utf-8") as file:
            assert any(message in msg for msg in file.readlines())
