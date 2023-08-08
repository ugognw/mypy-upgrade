"""This defines a tool to silence mypy errors using in-line comments.
"""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import argparse
import itertools
import pathlib
import shutil
import sys
import textwrap
from typing import NamedTuple

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.__about__ import __version__
from mypy_upgrade.filter import filter_mypy_errors
from mypy_upgrade.parsing import (
    MypyError,
    parse_mypy_report,
)
from mypy_upgrade.silence import silence_errors
from mypy_upgrade.utils import correct_line_numbers
from mypy_upgrade.warnings import (
    MISSING_ERROR_CODES,
    TRY_SHOW_ABSOLUTE_PATH,
    create_not_silenced_errors_warning,
)


class MypyUpgradeResult(NamedTuple):
    silenced: tuple[MypyError]
    not_silenced: tuple[MypyError]
    messages: tuple[str]


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
        "-V",
        "--version",
        default=False,
        action="store_const",
        const=True,
        help="Print the version.",
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
) -> MypyUpgradeResult:
    """Main logic for application.

    Args:
        report: an optional `pathlib.Path` pointing to the the mypy error
            report. If `None`, the report is read from the standard input.
        packages: a list of strings representing the packages in which to
            silence errors.
        modules: a list of strings representing the modules in which to
            silence errors.
        files: a list of strings representing the files in which to
            silence errors.
        description_style: a string specifying the style of error descriptions
            appended to the end of error suppression comments. A value of
            "full" appends the complete error message. A value of "none"
            does not append anything.
        fix_me: a string specifying the 'Fix Me' message in type error
            suppresion comments. Pass "" to omit a 'Fix Me' message
            altogether.

    Returns:
        A `MypyUpgradeResult` object. The errors that are silenced via type
        checking suppression comments are stored in the `silenced` attribute.
        Those that are unable to be silenced are stored in the `not_silenced`
        attribute. If a `FileNotFoundError` is raised while reading a file in
        which an error is to be silenced or `mypy-upgrade`-related warnings
        are raised during execution are stored in the `messages` attribute.
    """
    if report is not None:
        with pathlib.Path(report).open(encoding="utf-8") as file:
            errors = parse_mypy_report(file)
    else:
        errors = parse_mypy_report(sys.stdin)

    filtered_errors = filter_mypy_errors(errors, packages, modules, files)

    messages = []
    not_silenced: list[MypyError] = []
    silenced: list[MypyError] = []
    for filename, filename_grouped_errors in itertools.groupby(
        filtered_errors, key=lambda error: error.filename
    ):
        try:
            with pathlib.Path(filename).open(encoding="utf-8") as f:
                safe_to_silence, unsafe_to_silence = correct_line_numbers(
                    f, filename_grouped_errors
                )
                f.seek(0)
                lines = f.readlines()
        except FileNotFoundError:
            messages.append(
                TRY_SHOW_ABSOLUTE_PATH.replace("{filename}", filename)
            )
            return MypyUpgradeResult(
                tuple(silenced), tuple(not_silenced), tuple(messages)
            )

        not_silenced.extend(unsafe_to_silence)

        for line_number, line_grouped_errors in itertools.groupby(
            safe_to_silence, key=lambda error: error.line_no
        ):
            lines[line_number - 1] = silence_errors(
                lines[line_number - 1],
                line_grouped_errors,
                description_style,
                fix_me,
            )

        with pathlib.Path(filename).open(mode="w", encoding="utf-8") as f:
            _ = f.write("".join(lines))

        if safe_to_silence:
            silenced.extend(safe_to_silence)

    if any(error.error_code is None for error in silenced + not_silenced):
        messages.append(MISSING_ERROR_CODES)

    return MypyUpgradeResult(
        tuple(silenced), tuple(not_silenced), tuple(messages)
    )


def print_results(results: MypyUpgradeResult, verbosity: int) -> None:
    """Print the results contained in a `MypyUpgradeResult` object.

    Args:
        results: a `MypyUpgradeResult` object.
        verbosity: an integer specifying the verbosity.
    """
    width = min(79, shutil.get_terminal_size(fallback=(140, 0)).columns)

    def fill_(text: str) -> str:
        return textwrap.fill(text, width=width)

    if results.not_silenced:
        not_silenced_warning = create_not_silenced_errors_warning(
            results.not_silenced, verbosity
        )
        print(" WARNING ".center(width, "-"))  # noqa: T201
        print(fill_(not_silenced_warning))  # noqa: T201
        print()  # noqa: T201

    for message in results.messages:
        print(" WARNING ".center(width, "-"))  # noqa: T201
        print(fill_(message))  # noqa: T201
        print()  # noqa: T201

    if verbosity > 0:
        num_files = len({err.filename for err in results.silenced})
        num_silenced = len(results.silenced)
        text = fill_(
            f"{num_silenced} error{'' if num_silenced == 1 else 's'} "
            f"silenced across {num_files} file{'' if num_files == 1 else 's'}."
        )
        print(text)  # noqa: T201


def main() -> None:
    """An interface to `mypy_upgrade` from the command-line."""
    parser = _create_argument_parser()
    args = parser.parse_args()
    if args.version:
        print(f"mypy-upgrade {__version__}")  # noqa: T201
        return None

    try:
        results = mypy_upgrade(
            args.report,
            args.packages,
            args.modules,
            args.files,
            args.description_style,
            args.fix_me.strip(),
        )
    except FileNotFoundError as error:
        if error.filename == args.report:
            print(  # noqa: T201
                f"Aborting: Unable to find report {args.report}"
            )
        else:
            raise

    print_results(results, len(args.verbose))
