"""This module defines the CLI logic of `mypy-upgrade`."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import logging
import shutil
import sys
import textwrap
from collections.abc import Generator
from contextlib import contextmanager
from io import TextIOWrapper
from typing import NamedTuple, TextIO

from mypy_upgrade.parsing import MypyError

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.logging import ColouredFormatter
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report

logger = logging.getLogger()


class Options(NamedTuple):
    modules: list[str]
    packages: list[str]
    report: str | TextIOWrapper
    description_style: Literal["full", "none"]
    dry_run: bool
    fix_me: str
    verbosity: int
    summarize: bool
    colours: bool
    version: bool
    files: list[str]
    codes_to_silence: list[str] | None


@contextmanager
def _open(  # type: ignore[no-untyped-def]
    file: str | TextIO | TextIOWrapper, **kwargs
) -> Generator[TextIO, None, None]:
    if isinstance(file, (TextIOWrapper, TextIO)):
        resource = file
    else:
        resource = open(file, **kwargs)  # noqa: SIM115, PTH123

    try:
        yield resource
    finally:
        resource.close()


def _process_options(*args) -> Options:
    parser = argparse.ArgumentParser(
        prog="mypy-upgrade",
        usage="%(prog)s [-h] [-v] [-V] [more options; see below]\n"
        "                    [-m MODULE] [-p PACKAGE] [-r REPORT] "
        "[-s CODES_TO_SILENCE] "
        "[files ...]",
        description="""
Place in-line comments into files to silence mypy errors.
        """,
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

# Only silence "arg-type" errors
mypy --strict -p package > mypy_report.txt
mypy-upgrade --report mypy_report.txt  --silence-error arg-type
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        default=False,
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Don't actually silence anything, just print what would be.",
    )
    printing_group = parser.add_argument_group(
        title="Printing",
        description="Control what information is printed and how.",
    )
    verbosity = printing_group.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Control the verbosity. "
            "0=Print warnings and messages for each unsilenced error. "
            "1=Also print messages for each silenced error. "
            "2=Used for debugging. Defaults to 0."
        ),
        dest="verbosity",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        "--suppress-warnings",
        action="store_const",
        const=-1,
        dest="verbosity",
        help="Suppress all warnings. Disabled by default.",
    )
    printing_group.add_argument(
        "-S",
        "--summarize",
        action="store_true",
        default=False,
        help="Print a summary after running. If the verbosity is greater than "
        "zero, a detailed summary will also be printed. Disabled by default.",
    )
    printing_group.add_argument(
        "-c",
        "--colours",
        action="store_true",
        default=False,
        help="Enable coloured output. Disabled by default.",
    )
    comment_group = parser.add_argument_group(
        title="Comment Formatting",
        description="Format how error suppression comments are placed.",
    )
    comment_group.add_argument(
        "-d",
        "--description-style",
        default="none",
        choices=["full", "none"],
        help="""
        Specify the style in which mypy error descriptions are expressed in the
        error suppression comment. Defaults to "none".
        """,
    )
    comment_group.add_argument(
        "--fix-me",
        default="FIX ME",
        type=lambda x: x.rstrip(),
        help="""
        Specify a custom 'Fix Me' message to be placed after the error
        suppression comment. Pass " " to omit a 'Fix Me' message altogether.
        Defaults to "FIX ME".
        """,
    )
    filter_group = parser.add_argument_group(
        title="Error Filtering",
        description="Specify which errors will be silenced.",
    )
    filter_group.add_argument(
        "-r",
        "--report",
        default=sys.stdin,
        help="""
        The path to a text file containing a mypy type checking report. If not
        specified, input is read from standard input.
        """,
    )
    filter_group.add_argument(
        "-m",
        "--module",
        default=[],
        dest="modules",
        metavar="MODULE",
        action="append",
        help="Silence errors from the provided (importable) module. "
        "This flag may be repeated multiple times.",
    )
    filter_group.add_argument(
        "-p",
        "--package",
        default=[],
        dest="packages",
        metavar="PACKAGE",
        action="append",
        help="Silence errors from the provided (importable) package. "
        "This flag may be repeated multiple times.",
    )
    filter_group.add_argument(
        "-s",
        "--silence-error",
        action="append",
        dest="codes_to_silence",
        help="Silence mypy errors by error code. This flag may be repeated "
        "multiple times.",
    )
    filter_group.add_argument(
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return Options(**vars(parser.parse_args(*args)))


def summarize_results(*, results: MypyUpgradeResult, verbosity: int) -> None:
    """Print the results contained in a `MypyUpgradeResult` object.

    Args:
        results: a `MypyUpgradeResult` object.
        verbosity: an integer specifying the verbosity of the summary.
    """
    width = min(79, shutil.get_terminal_size(fallback=(79, 0)).columns)

    def _fill(text: str) -> str:
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
    print(_fill(not_silenced_warning))  # noqa: T201

    num_not_silenced = len(results.not_silenced)
    not_silenced_warning = (
        f"{num_not_silenced} {_to_verb(num_not_silenced)} not silenced due "
        "to syntax limitations."
    )
    print(_fill(not_silenced_warning))  # noqa: T201

    if verbosity > 0:
        print(" SILENCED ".center(width, "-"))  # noqa: T201
        for error in sorted(
            results.silenced, key=MypyError.filename_and_line_number
        ):
            print(str(error))  # noqa: T201

        print(" NOT SILENCED ".center(width, "-"))  # noqa: T201
        for error in sorted(
            results.not_silenced, key=MypyError.filename_and_line_number
        ):
            print(str(error))  # noqa: T201


def _configure_printing(*, verbosity: int, colours: bool) -> None:
    level = 30 - (verbosity * 10)
    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)

    fmt = "%(message)s"
    formatter = ColouredFormatter(fmt) if colours else logging.Formatter(fmt)

    ch.setFormatter(formatter)

    logger.addHandler(ch)


def main() -> None:
    """An interface to `mypy-upgrade` from the command-line."""
    options = _process_options()
    _configure_printing(
        verbosity=options.verbosity,
        colours=options.colours,
    )

    with _open(file=options.report, mode="r", encoding="utf-8") as report:
        results = silence_errors_in_report(
            report=report,
            packages=options.packages,
            modules=options.modules,
            files=options.files,
            codes_to_silence=options.codes_to_silence,
            description_style=options.description_style,
            fix_me=options.fix_me,
            dry_run=options.dry_run,
        )

    if options.summarize:
        summarize_results(results=results, verbosity=options.verbosity)
