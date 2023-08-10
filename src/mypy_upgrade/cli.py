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
    silenced: tuple[MypyError, ...]
    not_silenced: tuple[MypyError, ...]
    messages: tuple[str, ...]


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
        specified, input is read from standard input. Defaults to stdin.
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
            altogether. All trailing whitespace will be trimmed.

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
            args.fix_me.rstrip(),
        )
    except FileNotFoundError as error:
        if error.filename == str(args.report):
            print(  # noqa: T201
                f"Aborting: Unable to find report {args.report}"
            )
            return None
        else:
            raise

    options = {
        "verbosity": args.verbosity,
        "suppress_warnings": args.suppress_warnings,
    }
    print_results(results, options=options)
