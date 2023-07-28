#!/usr/bin/env python3

"""This defines a tool to silence mypy errors using in-line comments.


Usage::

    $ mypy path/to/project | ./mypy-upgrade <package>
"""

import argparse
import fileinput
import re
import sys


def process_report(package: str) -> dict[str, list[tuple[int, str]]]:
    """
    Parses a mypy error report.

    Args:
        package: a string representing the package name used in import statements.

    Returns:
        A dictionary representing the mypy errors in each module in which each key is a
        string representing the path to a module containing a mypy error and each
        corresponding value is a list of two-tuples whose first and second entries are an integer
        representing the line number of the error and a string representing the mypy error code,
        respectively.

        Usage::

           errors = process_report('ase')
           line_no, error_code = errors['ase/atoms.py']
    """
    del sys.argv[1]  # ensure fileinput works as expected; there's gotta be a better way to do this
    # captures: 1) file path 2) line number 3) error code
    info = re.compile(r"(" + re.escape(package) + r"/[^:]+):(\d+):.+\[(.+)\]$")
    errors = {}

    with fileinput.input() as report:
        for line in report:
            package_error = info.search(line)
            if package_error:
                module, error_code = package_error.group(1, 3)
                line_no = int(package_error.group(2))
                if module not in errors:
                    errors[module] = []

                errors[module].append((line_no, error_code))

    return errors


def silence_error(file: str, errors: list[tuple[int, str]]):
    """
    Silences all errors in a given file.

    Args:
        file: a string representing the path to the module with the errors to fix.
        errors: a list of two-tuples representing the errors in the given module wherein
            for each tuple, the first entry is an int representing the line number (1-indexed)
            and the second entry is a string representing the error code.
    """
    with open(file, mode='r', encoding="utf-8") as f:
        lines = f.readlines()

    for line_no, error_code in errors:
        line = lines[line_no - 1].removesuffix("\n")
        lines[line_no - 1] = f"{line}  # type: ignore[{error_code}]\n"

    with open(file, "w", encoding="utf-8") as f:
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
    errors = process_report(args.package)
    for module in errors:
        silence_error(module, errors[module])

    silenced = sum(map(len, errors.values()))
    print(f"{silenced} errors silenced across {len(errors)} modules.")


if __name__ == "__main__":
    main()
