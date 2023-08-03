"""This defines a tool to silence mypy errors using in-line comments.
"""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import itertools
import pathlib
import sys

from typing_extensions import Literal  # import from typing for Python 3.8+

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
        action="append",
        help="Silence errors from the provided (importable) module. "
        "This flag may be repeated multiple times.",
    )
    parser.add_argument(
        "-p",
        "--package",
        default=[],
        dest="packages",
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
        specified, input is read from stdin.
        """,
    )
    parser.add_argument(
        "-d",
        "--with-descriptions",
        action="store_const",
        const="description",
        dest="suffix",
        help="""
        Use this flag to include the mypy error descriptions in the error
        suppression comment.
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
    suffix: Literal["description"] | None,
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
        suffix: an optional string specifying the type of suffix.

    Returns:
        A two-tuple whose first element is a list of MypyErrors that were
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
    for filename, filename_grouped_errors in itertools.groupby(
        filtered_errors, key=lambda error: error.filename
    ):
        with pathlib.Path(filename).open(encoding="utf-8") as f:
            line_number_corrected_errors, lines = correct_line_numbers(
                f, filename_grouped_errors
            )

        for line_number, line_grouped_errors in itertools.groupby(
            line_number_corrected_errors, key=lambda error: error.line_no
        ):
            lines[line_number - 1] = silence_errors(
                lines[line_number - 1], line_grouped_errors, suffix
            )

        with pathlib.Path(filename).open(mode="w", encoding="utf-8") as f:
            _ = f.write("".join(lines))

        edited_files.append(filename)

    return filtered_errors, edited_files


def main() -> None:
    """Logic for CLI."""
    parser = _create_argument_parser()
    args = parser.parse_args()
    errors, modules = mypy_upgrade(
        args.report,
        args.packages,
        args.modules,
        args.files,
        args.suffix,
    )

    if len(args.verbose) > 0:
        print(  # noqa: T201
            f"{len(errors)} errors silenced across {len(modules)} modules."
        )
