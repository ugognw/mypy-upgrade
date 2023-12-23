"""This module defines the CLI logic of `mypy-upgrade`."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import logging
import pathlib
import shutil
import sys
import textwrap
from typing import NamedTuple, TextIO

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.logging import ColouredFormatter
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report

logger = logging.getLogger()


class Options(NamedTuple):
    modules: list[str]
    packages: list[str]
    report: TextIO
    description_style: str
    dry_run: bool
    fix_me: str
    verbosity: int
    summarize: bool
    colours: bool
    version: bool
    suppress_warnings: bool
    files: list[str]
    error_codes_to_silence: tuple[str]


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
        filename = pathlib.Path(values)
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
        default=sys.stdin,
        type=argparse.FileType(
            mode="r", encoding="utf-8"
        ),  # find safer way to open
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
        "-q",
        "--quiet",
        "--suppress-warnings",
        default=False,
        dest="suppress_warnings",
        action="store_true",
        help="Suppress all warnings. Disabled by default.",
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
        "-S",
        "--summarize",
        action="store_true",
        default=False,
        help="Print a summary after running.",
    )
    parser.add_argument(
        "-c",
        "--colours",
        action="store_true",
        default=False,
        help="Enable coloured output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Don't actually silence anything, just print what would be.",
    )
    parser.add_argument(
        "-s",
        "--silence-error",
        action="append",
        default=[],
        dest="error_codes_to_silence",
        help="Silence mypy errors by error code. This flag may be repeated "
        "multiple times.",
    )
    parser.add_argument(
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return parser


def summarize_results(*, results: MypyUpgradeResult) -> None:
    """Print the results contained in a `MypyUpgradeResult` object.

    Args:
        results: a `MypyUpgradeResult` object.
    """
    width = min(79, shutil.get_terminal_size(fallback=(79, 0)).columns)

    def fill_(text: str) -> str:
        return textwrap.fill(text, width=width)

    def _to_verb(count: int) -> str:
        if count == 1:
            return "error was"
        return "errors were"

    print(" SUMMARY ".center(width, "-"))  # noqa: T201

    num_silenced = len(results.silenced)
    not_silenced_warning = (
        f"{num_silenced} {_to_verb(num_silenced)} silenced.\n\n"
    )
    print(fill_(not_silenced_warning))  # noqa: T201

    num_not_silenced = len(results.not_silenced)
    not_silenced_warning = (
        f"{num_not_silenced} {_to_verb(num_not_silenced)} not silenced due "
        "to syntax limitations."
    )
    print(fill_(not_silenced_warning))  # noqa: T201


def _configure_printing(
    *, suppress_warnings: bool, verbosity: int, colours: bool
) -> None:
    if suppress_warnings:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG

    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    fmt = "%(levelname)s:%(message)s"
    formatter = ColouredFormatter(fmt) if colours else logging.Formatter(fmt)

    ch.setFormatter(formatter)

    logger.addHandler(ch)


def main() -> None:
    """An interface to `mypy-upgrade` from the command-line."""
    parser = _create_argument_parser()
    options = Options(**vars(parser.parse_args()))
    _configure_printing(
        suppress_warnings=options.suppress_warnings,
        verbosity=options.verbosity,
        colours=options.colours,
    )

    results = silence_errors_in_report(
        report=options.report,
        packages=options.packages,
        modules=options.modules,
        files=options.files,
        error_codes_to_silence=options.error_codes_to_silence,
        description_style=options.description_style,
        fix_me=options.fix_me.rstrip(),
        dry_run=options.dry_run,
    )
    if options.summarize:
        summarize_results(results=results)
