"""This defines a tool to silence mypy errors using in-line comments.
"""

import argparse
import pathlib
import re
import sys
import typing
from importlib import util


def parse_report(
    report: typing.TextIO,
) -> list[tuple[str, int, str, str]]:
    """Parse a mypy error report from stdin.

    Args:
        report: a text stream from which to read the mypy typing report
    Returns:
        A list of four-tuples which represent a mypy error. The elements of
        the tuple are as follows:

            0. a string representing the path to module containing the error

            1. an int representing the line number (1-indexed) of the error

            2. a string representing the mypy error code

            3. a string describing the error

        Example::

           >> errors = process_report('ase')
           >> module, line_no, error_code, description = errors[0]
    """
    info = re.compile(r"^([^:]+):(\d+): error: (.+)\s+(?:\[(.+)\])?\n$")
    errors = []

    for line in report:
        package_error = info.match(line)
        if package_error:
            module, description, error_code = package_error.group(1, 3, 4)
            line_no = int(package_error.group(2))
            errors.append((module, line_no, error_code, description))

    return errors


def get_module_paths(modules: list[str]) -> list[pathlib.Path | None]:
    """Determine file system paths of given modules/packages.

    Args:
        modules: a list of strings representing (importable) modules.

    Returns:
        A list (of the same length as the input list) of pathlib.Path objects
        corresponding to the given modules. If a path is not found for a
        module, the corresponding entry in the output is ``None``.
    """
    paths: list[pathlib.Path | None] = []
    for module in modules:
        spec = util.find_spec(module)
        if spec is None:
            paths.append(None)
        else:
            origin = spec.origin
            if spec.submodule_search_locations:  # Package
                if origin is None:  # Namespace
                    module_path = pathlib.Path(
                        spec.submodule_search_locations[0]
                    )
                else:  # Regular
                    module_path = pathlib.Path(
                        origin.removesuffix("__init__.py")
                    )
            elif origin is None:  # Something weird has happened
                module_path = None
            else:  # Module
                module_path = pathlib.Path(origin)

            paths.append(module_path)

    return paths


def select_errors(
    errors: list[tuple[str, int, str, str]],
    packages: list[str],
    modules: list[str],
    files: list[str],
) -> list[tuple[str, int, str, str]]:
    """Select errors based on specified packages, modules, files.

    Args:
        errors: a list of tuples of the form of the output of ``parse_report``.
        packages: a list of strings specifying packages to be included.
        modules: a list of strings specifying modules to be included.
        files: a list of strings specifying files to be included.

    Returns:
        A list of errors including only those in either ``packages``,
        ``modules``, or ``files``.
    """
    package_paths = [p for p in get_module_paths(packages) if p is not None]
    module_paths = [m for m in get_module_paths(modules) if m is not None]
    paths = package_paths + module_paths + files
    selected = []
    for module, line_no, error_code, description in errors:
        module_path = pathlib.Path(module).resolve()
        should_include = False
        for path in paths:
            if pathlib.Path(module_path).is_relative_to(path):
                should_include = True
                break

        if should_include:
            selected.append((module, line_no, error_code, description))

    return selected


def extract_old_error(line: str) -> tuple[str | None, str | None, str | None]:
    """Extract error code and description from mypy error suppression comment.

    Args:
        line: a string representing a line to search.

    Returns:
        A tuple containing the whole error suppressing comment, the error code
        and the description. If either the error code or the description is
        not found, its corresponding entry is ``None``.
    """
    comment = code = description = None
    suppressed = re.search(
        r"(#\s*type:\s*ignore(?:\[\s*([\s\w,\-]+)\s*\])?\s*\#*\s*(.*))", line
    )
    if suppressed:
        comment = suppressed.group(1) or None
        code = suppressed.group(2) or None
        description = suppressed.group(3) or None

    return comment, code, description


def silence_error(line: str, error_code: str, description: str) -> str:
    """Silences the given error on a line with an error code-specific comment.

    Args:
        line: a string containing the line.
        error_code: a string representing the mypy error code.
        description: a string representing a description of the error.
    Returns:
        The line with a type error suppression comment.
    """
    old_comment, old_code, old_description = extract_old_error(line)

    if old_comment is not None:
        line = line.replace(old_comment, "")

    if old_code and error_code:
        error_code = ",".join((old_code.strip(), error_code))
    else:
        error_code = old_code if old_code else error_code

    if old_description and description:
        description = ", ".join((old_description.strip(), description))
    else:
        description = old_description if old_description else description

    code_annotation = f"[{error_code}]" if error_code else ""
    comment = f"# type: ignore{code_annotation}  # {description}"
    return f"{line}  {comment}\n"


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mypy-upgrade",
        description="""
        Place in-line comments into files to silence mypy errors.
        """,
        epilog="""
    # Pyre-like invocation
    $ mypy -p ase | python -m mypy_upgrade --package ase

    # Use saved report file
    $ mypy -p ase > mypy_report.txt
    $ pythom -m mypy_upgrade --package ase --report mypy_report.txt

    # Only silence errors in subpackage
    $ mypy -p ase > mypy_report.txt
    $ pythom -m mypy_upgrade --package ase.build --report mypy_report.txt

    # Only silence errors in modules
    $ mypy -p ase > mypy_report.txt
    $ pythom -m mypy_upgrade --module ase.atoms --report mypy_report.txt

    # Only silence errors in file
    $ mypy -p ase > mypy_report.txt
    $ pythom -m mypy_upgrade --report mypy_report.txt ase/atoms.py

    # Only silence errors in directory
    $ mypy -p ase > mypy_report.txt
    $ pythom -m mypy_upgrade --report mypy_report.txt doc
        """,
    )
    parser.add_argument(
        "-m",
        "--module",
        default=[],
        action="append",
        help="Silence errors from the provided (importable) module. "
        "This flag may be repeated multiple times.",
    )
    parser.add_argument(
        "-p",
        "--package",
        default=[],
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
        "files",
        default=[],
        nargs="*",
        help="Silence errors from the provided files/directories.",
    )
    return parser.parse_args()


def main():
    """Logic for CLI."""
    args = _parse_arguments()

    if args.report is not None:
        with open(args.report) as report:
            errors = parse_report(report)
    else:
        errors = parse_report(sys.stdin)

    selected = select_errors(errors, args.package, args.module, args.files)
    modules = []
    for module, line_no, error_code, description in selected:
        with open(module, encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[line_no - 1].removesuffix("\n")
        line = silence_error(line, error_code, description)
        lines[line_no - 1] = line

        with open(module, "w", encoding="utf-8") as f:
            _ = f.write("".join(lines))

        if module not in modules:
            modules.append(module)

    print(  # noqa: T201
        f"{len(selected)} errors silenced across {len(modules)} modules."
    )
