#!/usr/bin/env python3

"""This defines a tool to silence mypy errors using in-line comments.


Usage::

    $ mypy path/to/project | pythom -m mypy-upgrade <package>
"""

import argparse
import fileinput
import re
import sys


def process_piped_report(package: str) -> list[tuple[str, int, str, str]]:
    """
    Parse a mypy error report from stdin.

    Args:
        package: a string representing the package name used in import
            statements.

    Returns:
        A list of four-tuples which represent a mypy error. The elements of
        the tuple are as follows:
            0) a string representing the path to module containing the error
            1) an int representing the line number of the error
            2) a string representing the mypy error code
            3) a string describing the error
        Note that the line numbers are 1-indexed.

        Example::

           >> errors = process_report('ase')
           >> module, line_no, error_code, description = errors[0]
    """
    # ensure fileinput works as expected; there's gotta be a better way to do this
    del sys.argv[1]
    # captures:
    # 1) file path to module
    # 2) line number
    # 3) error description
    # 4) error code
    info = re.compile(
        r"(" + re.escape(package) + r"/[^:]+):(\d+): error: (.+)\s+\[(.+)\]$"
    )
    errors = []

    with fileinput.input() as report:
        for line in report:
            package_error = info.search(line)
            if package_error:
                module, description, error_code = package_error.group(1, 3, 4)
                line_no = int(package_error.group(2))
                errors.append((module, line_no, error_code, description))

    return errors


def silence_errors(
    module: str, line_no: int, error_code: str, description: str
):
    """
    Silences all errors in a given file.

    Args:
        module: a string representing the path to the module with the errors
            to fix.
        errors: a dictionary representing the errors in a module in the same
            format as the values of the return vale of `process_piped_report`.
    """
    with open(module, mode="r", encoding="utf-8") as f:
        lines = f.readlines()

    line = lines[line_no - 1].removesuffix("\n")
    comment = f"# type: ignore[{error_code}]  # {description}"
    lines[line_no - 1] = f"{line}  {comment}\n"

    with open(module, "w", encoding="utf-8") as f:
        _ = f.write("".join(lines))


def main():
    parser = argparse.ArgumentParser(
        prog="mypy-upgrade",
        description="Place in-line comments into files to silence mypy errors",
        epilog="""
Usage::

    $ mypy /path/to/project | ./mypy-upgrade <package-name>
""",
    )
    parser.add_argument("package")
    args = parser.parse_args()
    errors = process_piped_report(args.package)
    modules = []
    for module, line_no, error_code, description in errors:
        silence_errors(module, line_no, error_code, description)
        if module not in modules:
            modules.append(module)

    print(f"{len(errors)} errors silenced across {len(modules)} modules.")


if __name__ == "__main__":
    main()
