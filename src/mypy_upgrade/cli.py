"""This defines a tool to silence mypy errors using in-line comments.
"""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import itertools
import pathlib
import sys

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.filter import filter_mypy_errors
from mypy_upgrade.parsing import (
    MypyError,
    parse_mypy_report,
)
from mypy_upgrade.silence import silence_errors
from mypy_upgrade.utils import correct_line_numbers


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

Pyre-like invocation
$ mypy --strict -p ase | mypy-upgrade

Use saved report file
$ mypy --strict -p ase > mypy_report.txt
$ mypy-upgrade --report mypy_report.txt

Only silence errors in package/module
$ mypy --strict -p ase > mypy_report.txt
$ mypy-upgrade -p ase.build -m ase.atoms --report mypy_report.txt

Only silence errors in file/directory
$ mypy --strict -p ase > mypy_report.txt
$ mypy-upgrade --report mypy_report.txt ase/atoms.py doc
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
        error suppression comment.
        """,
    )
    parser.add_argument(
        "--fix-me",
        default="FIX ME",
        help="""
        Specify a custom 'Fix Me' message to be placed after the error
        suppression comment. Pass " " to omit a 'Fix Me' message altogether.
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="append_const",
        const=True,
        default=[],
        help="Control the verbosity.",
    )
    parser.add_argument(
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return parser


def mypy_upgrade(
    report: pathlib.Path | None,
    packages: list[str],
    modules: list[str],
    files: list[str],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> tuple[list[MypyError], list[str]]:
    """Main logic for application.

    Args:
        report: a text file object representing the mypy error report.
        packages: a list of string representing the packages in which to
            silence errors.
        modules: a list of string representing the modules in which to
            silence errors.
        files: a list of string representing the files in which to
            silence errors.
        description_style: a string specifying the style of error descriptions
            appended to the end of error suppression comments.
        fix_me: a string specifying the 'Fix Me' message in type error
            suppresion comments. Pass " " to omit a 'Fix Me' message
            altogether.

    Returns:
        A 2-tuple whose first element is a list of MypyErrors that were
        silenced and whose second element is the list of modules in which
        errors were silenced.
    """
    if report is not None:
        with pathlib.Path(report).open(encoding="utf-8") as file:
            errors = parse_mypy_report(file)
    else:
        errors = parse_mypy_report(sys.stdin)

    filtered_errors = filter_mypy_errors(errors, packages, modules, files)

    edited_files = []
    excluded = []  # Do something with these
    silenced_errors = []
    for filename, filename_grouped_errors in itertools.groupby(
        filtered_errors, key=lambda error: error.filename
    ):
        with pathlib.Path(filename).open(encoding="utf-8") as f:
            safe_to_suppress, to_exclude = correct_line_numbers(
                f, filename_grouped_errors
            )
            f.seek(0)
            lines = f.readlines()

        excluded.extend(to_exclude)

        for line_number, line_grouped_errors in itertools.groupby(
            safe_to_suppress, key=lambda error: error.line_no
        ):
            lines[line_number - 1] = silence_errors(
                lines[line_number - 1],
                line_grouped_errors,
                description_style,
                fix_me.strip(),
            )

        with pathlib.Path(filename).open(mode="w", encoding="utf-8") as f:
            _ = f.write("".join(lines))

        if safe_to_suppress:
            edited_files.append(filename)
            silenced_errors.extend(safe_to_suppress)

    return silenced_errors, edited_files


def main() -> None:
    """Logic for CLI."""
    parser = _create_argument_parser()
    args = parser.parse_args()
    errors, modules = mypy_upgrade(
        args.report,
        args.packages,
        args.modules,
        args.files,
        args.description_style,
        args.fix_me.strip(),
    )

    if len(args.verbose) > 0:
        print(  # noqa: T201
            f"{len(errors)} errors silenced across {len(modules)} modules."
        )
