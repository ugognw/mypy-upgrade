"""This module defines the CLI logic of `mypy-upgrade`."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys
import textwrap

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.silence import MypyUpgradeResult, silence_errors_in_report
from mypy_upgrade.warnings import (
    create_not_silenced_errors_warning,
)


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
        action="store_const",
        const=True,
        help="Print the version.",
    )
    parser.add_argument(
        "--suppress-warnings",
        default=False,
        action="store_const",
        const=True,
        help="Suppress all warnings. Disabled by default.",
    )
    parser.add_argument(
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return parser


def print_results(
    results: MypyUpgradeResult, options: dict[str, int | bool]
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

    if results.not_silenced and not options["suppress_warnings"]:
        not_silenced_warning = create_not_silenced_errors_warning(
            results.not_silenced, options["verbosity"]
        )
        print(" WARNING ".center(width, "-"))  # noqa: T201
        print(fill_(not_silenced_warning))  # noqa: T201
        print()  # noqa: T201

    if not options["suppress_warnings"]:
        for message in results.messages:
            print(" WARNING ".center(width, "-"))  # noqa: T201
            print(fill_(message))  # noqa: T201
            print()  # noqa: T201

    if options["verbosity"] == 1:
        num_files = len({err.filename for err in results.silenced})
        num_silenced = len(results.silenced)
        text = fill_(
            f"{num_silenced} error{'' if num_silenced == 1 else 's'} "
            f"silenced across {num_files} file{'' if num_files == 1 else 's'}."
        )
        print(text)  # noqa: T201
    elif options["verbosity"] > 1:
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


def main() -> None:
    """An interface to `mypy-upgrade` from the command-line."""
    parser = _create_argument_parser()
    args = parser.parse_args()
    if args.version:
        print(f"mypy-upgrade {__version__}")  # noqa: T201
        return None

    if args.report is None:
        results = silence_errors_in_report(
            sys.stdin,
            args.packages,
            args.modules,
            args.files,
            args.description_style,
            args.fix_me.rstrip(),
        )
    else:
        report: pathlib.Path = args.report
        with report.open(mode="r", encoding="utf-8") as file:
            results = silence_errors_in_report(
                file,
                args.packages,
                args.modules,
                args.files,
                args.description_style,
                args.fix_me.rstrip(),
            )

    options = {
        "verbosity": args.verbosity,
        "suppress_warnings": args.suppress_warnings,
    }
    print_results(results, options=options)
