"""This module defines the CLI logic of `mypy-upgrade`."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import logging
import pathlib
import shutil
import sys
import textwrap
from collections.abc import Mapping
from logging import _FormatStyle
from typing import Any, NamedTuple, TextIO

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report
from mypy_upgrade.warnings import (
    create_not_silenced_errors_warning,
)

DEFAULT_COLOURS = {
    logging.DEBUG: 36,
    logging.INFO: 33,
    logging.WARNING: 95,
    logging.ERROR: 35,
    logging.CRITICAL: 31,
}


logger = logging.getLogger(__name__)


class ColouredFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: _FormatStyle = "%",
        validate: bool = True,  # noqa: FBT001, FBT002
        *,
        defaults: Mapping[str, Any] | None = None,
        colours: dict[int, str] | None = None,
    ) -> None:
        self.colours = colours or DEFAULT_COLOURS
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def formatMessage(self, record: logging.LogRecord):  # noqa: N802
        colour_code = self.colours[record.levelno]
        return f"\033[1;{colour_code}m{self._style.format(record)}\033[0m"


class _Options(NamedTuple):
    modules: list[str]
    packages: list[str]
    report: TextIO
    description_style: str
    dry_run: bool
    fix_me: str
    verbosity: int
    version: bool
    suppress_warnings: bool
    files: list[str]


class FileAction(argparse.Action):
    """Represents a file to be opened for reading"""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            msg = "nargs not allowed"
            raise ValueError(msg)
        super().__init__(option_strings, dest, **kwargs)

    def __call__(
        self, parser, namespace, values, option_string=None  # noqa: ARG002
    ):
        filename = pathlib.Path(values[0])
        with filename.open(mode="r", encoding="utf-8") as file:
            setattr(namespace, self.dest, file)


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mypy-upgrade",
        description="""
Place in-line comments into files to silence mypy errors.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------

# Pyre-like invocation
mypy --strict -p package | mypy-upgrade

# Use saved report file
mypy --strict -p package > mypy_report.txt
mypy-upgrade --report mypy_report.txt

# Only silence errors in package/module
mypy --strict -p package > mypy_report.txt
mypy-upgrade -p package.subpackage -m package.module --report mypy_report.txt

# Only silence errors in file/directory
mypy --strict -p package > mypy_report.txt
mypy-upgrade --report mypy_report.txt package/module.py package/
""",
    )
    parser.add_argument(
        "-m",
        "--module",
        default=[],
        dest="modules",
        metavar="MODULE",
        action="append",
        help="Silence errors from the provided (importable) module. "
        "This flag may be repeated multiple times.",
    )
    parser.add_argument(
        "-p",
        "--package",
        default=[],
        dest="packages",
        metavar="PACKAGE",
        action="append",
        help="Silence errors from the provided (importable) package. "
        "This flag may be repeated multiple times.",
    )
    parser.add_argument(
        "-r",
        "--report",
        action=FileAction,
        default=sys.stdin,
        type=pathlib.Path,
        help="""
        The path to a text file containing a mypy type checking report. If not
        specified, input is read from standard input.
        """,
    )
    parser.add_argument(
        "-d",
        "--description-style",
        default="none",
        choices=["full", "none"],
        help="""
        Specify the style in which mypy error descriptions are expressed in the
        error suppression comment. Defaults to "none".
        """,
    )
    parser.add_argument(
        "--fix-me",
        default="FIX ME",
        help="""
        Specify a custom 'Fix Me' message to be placed after the error
        suppression comment. Pass " " to omit a 'Fix Me' message altogether.
        Defaults to "FIX ME".
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help=(
            "Control the verbosity. "
            "0: Only warnings are printed. "
            "1: Print detailed warnings, a short summary of silenced errors, "
            "and a detailed list of errors that were not silenced. "
            "2: Print detailed warnings, a detailed list of silenced errors, "
            "and a detailed list of errors that were not silenced. Defaults "
            "to 0. "
            "This flag may be repeated multiple times."
        ),
    )
    parser.add_argument(
        "-V",
        "--version",
        default=False,
        action="version",
        version=f"%(prog)s {__version__}",
        help="Print the version.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        "--suppress-warnings",
        default=False,
        dest="suppress_warnings",
        action="store_const",
        const=True,
        help="Suppress all warnings. Disabled by default.",
    )
    parser.add_argument(
        "--dry-run",
        default=False,
        action="store_const",
        const=True,
        help="Don't actually silence anything, just print what would be.",
    )
    parser.add_argument(
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return parser


def summarize_results(
    *, results: MypyUpgradeResult, options: _Options
) -> None:
    """Print the results contained in a `MypyUpgradeResult` object.

    Args:
        results: a `MypyUpgradeResult` object.
        options: a dictionary containing the following keys:
            verbosity: an integer specifying the verbosity
            suppress_warnings: a boolean indicating whether to suppress
                warnings
    """
    width = min(79, shutil.get_terminal_size(fallback=(79, 0)).columns)

    def fill_(text: str) -> str:
        return textwrap.fill(text, width=width)

    if results.not_silenced and not options.suppress_warnings:
        not_silenced_warning = create_not_silenced_errors_warning(
            not_silenced=results.not_silenced, verbosity=options.verbosity
        )
        print(" WARNING ".center(width, "-"))  # noqa: T201
        print(fill_(not_silenced_warning))  # noqa: T201
        print()  # noqa: T201

    if options.verbosity == 1:
        num_files = len({err.filename for err in results.silenced})
        num_silenced = len(results.silenced)
        text = fill_(
            f"{num_silenced} error{'' if num_silenced == 1 else 's'} "
            f"silenced across {num_files} file{'' if num_files == 1 else 's'}."
        )
        print(text)  # noqa: T201
    elif options.verbosity > 1:
        if results.silenced:
            print(  # noqa: T201
                f" ERRORS SILENCED ({len(results.silenced)}) ".center(
                    width, "-"
                )
            )
            for error in results.silenced:
                print(  # noqa: T201
                    f"{error.error_code}: {error.filename} ({error.line_no})"
                )
        if results.not_silenced:
            print(  # noqa: T201
                f" ERRORS NOT SILENCED ({len(results.not_silenced)}) ".center(
                    width, "-"
                )
            )
            for error in results.not_silenced:
                print(  # noqa: T201
                    f"{error.error_code}: {error.filename} ({error.line_no})"
                )


def _configure_printing(*, suppress_warnings: bool, verbosity: int) -> None:
    if suppress_warnings:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG

    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    formatter = ColouredFormatter("%(levelname)s:%(message)s")

    ch.setFormatter(formatter)

    logger.addHandler(ch)


def main() -> None:
    """An interface to `mypy-upgrade` from the command-line."""
    parser = _create_argument_parser()
    options: _Options = parser.parse_args()
    _configure_printing(
        suppress_warnings=options.suppress_warnings,
        verbosity=options.verbosity,
    )

    results = silence_errors_in_report(
        report=options.report,
        packages=options.packages,
        modules=options.modules,
        files=options.files,
        description_style=options.description_style,
        fix_me=options.fix_me.rstrip(),
        dry_run=options.dry_run,
    )
    summarize_results(results=results, options=options)
