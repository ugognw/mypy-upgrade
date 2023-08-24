# `mypy-upgrade`

[![PyPI - Version](https://img.shields.io/pypi/v/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![Wheel Support](https://img.shields.io/pypi/wheel/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![Supported Implementations](https://img.shields.io/pypi/implementation/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![Tests](https://github.com/ugognw/mypy-upgrade/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ugognw/mypy-upgrade/actions)
[![Coverage](https://coveralls.io/repos/github/ugognw/mypy-upgrade/badge.svg?branch=main)](https://coveralls.io/github/ugognw/mypy-upgrade?branch=main)
[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)

-----

**Table of Contents**

- [What is `mypy-upgrade`?](#what-is-mypy-upgrade)
- [Features](#features)
- [Basic Usage](#basic-usage)
- [Recommended Mypy Flags](#recommended-mypy-flags)
- [Using the API](#using-the-api)
- [Command-Line Options](#command-line-options)
- [Quick Start](#quick-start)
- [Known Limitations](#known-limitations)
- [Similar Projects](#similar-projects)

## What is `mypy-upgrade`?

`mypy-upgrade` is primarily a command-line utility that provides automatic
error suppression for [`mypy`](http://mypy.readthedocs.io/) (analogous to
[`pyre-upgrade`](https://pyre-check.org/docs/types-in-python/#upgrade) and
[`pylint-silent`](https://github.com/udifuchs/pylint-silent/)). In addition,
`mypy-upgrade` exposes an API with the same functionality.

Given a type checking report from `mypy`, `mypy-upgrade` will silence
the listed errors using error suppression comments. For example, with
the following output from mypy:

    package/subpackage/module.py:13: error: Incompatible default for argument "filename" (default has type "None", argument has type "str") [assignment]

`mypy-upgrade` will place a `# type: ignore[assignment] # FIX ME` comment at the
end of line 13 in `package/subpackage/module.py`. If error codes are not
present in the `mypy` report (e.g., the `--hide-error-codes` flag is set when
`mypy` was invoked), then a non-specific `# type: ignore # FIX ME` comment will be
added instead.

## Features

* Removal of unused `type: ignore` comments

* Replacement of blanket `type: ignore` comments with error code-specific
comments

* Support for suppressing multiple mypy errors per-line

* Preservation of existing in-line comments

* Optional inclusion of `mypy` error description messages

## Basic Usage

There are two idioms for invocation. To silence all errors in a package, one
can:

1. pipe `mypy`'s output directly to `mypy-upgrade`

        mypy --strict -p my_package | mypy-upgrade

2. create a `mypy` type checking report text file

        mypy --strict -p my_package > mypy_report.txt

    and then pass the file to `mypy-upgrade`

        mypy-upgrade --report mypy_report.txt

## Command-Line Options

You may want to include the error messages provided by `mypy` in the
suppression comments so that you can fix them later. You can do so using
the `-d` (or `--description-style`) option

    mypy-upgrade --report mypy_report.txt -d full -p package

You can also customize the "fix me" message placed after the error suppression
comment using the `--fix-me` option

    mypy-upgrade --report mypy_report.txt --fix-me "FIX THIS" -p package

To selectively silence errors in packages and modules, use the `-p`
(`--package`) and `-m` (`--module`) options along with the fully qualified
module/package name, respectively:

    mypy-upgrade --report mypy_report.txt -p package1 -p package2 -m package1.module1 -m package2.module2

Similarly, to selectively silence errors in files and directories,
pass them in as positional arguments:

    mypy-upgrade --report mypy_report.txt path/to/a/package/ path/to/a/module.py

For a full list of all options and their descriptions, run

    mypy-upgrade --help

    usage: mypy-upgrade [-h] [-m MODULE] [-p PACKAGE] [-r REPORT] [-d {full,none}] [--fix-me FIX_ME] [-v] [-V] [--suppress-warnings] [files ...]

    Place in-line comments into files to silence mypy errors.


    positional arguments:
    files                 Silence errors from the provided files/directories.

    options:
    -h, --help            show this help message and exit
    -m MODULE, --module MODULE
                            Silence errors from the provided (importable) module. This flag may be repeated multiple times.
    -p PACKAGE, --package PACKAGE
                            Silence errors from the provided (importable) package. This flag may be repeated multiple times.
    -r REPORT, --report REPORT
                            The path to a text file containing a mypy type checking report. If not specified, input is read from standard input.
    -d {full,none}, --description-style {full,none}
                            Specify the style in which mypy error descriptions are expressed in the error suppression comment. Defaults to "none".
    --fix-me FIX_ME       Specify a custom 'Fix Me' message to be placed after the error suppression comment. Pass " " to omit a 'Fix Me' message altogether. Defaults to
                            "FIX ME".
    -v, --verbose         Control the verbosity. 0: Only warnings are printed. 1: Print detailed warnings, a short summary of silenced errors, and a detailed list of errors
                            that were not silenced. 2: Print detailed warnings, a detailed list of silenced errors, and a detailed list of errors that were not silenced.
                            Defaults to 0. This flag may be repeated multiple times.
    -V, --version         Print the version.
    --suppress-warnings   Suppress all warnings. Disabled by default.

## Using the API

Identical functionality to the command-line utility can be obtained using the
API. In addition, one obtains detailed information on the results of running
`mypy-upgrade`.  Assuming the `mypy` type checking report is saved as
`mypy_report.txt`

    import pathlib

    from mypy_upgrade.silence import silence_errors_in_report

    mypy_report = pathlib.Path("mypy_report.txt")

    with mypy_report.open(mode="r", encoding="utf-8") as report:
        result = silence_errors_in_report(
            report=report
            packages=["package1", "package2"],
            modules=["package1.module1", "package2.module2"],
            files=["path/to/a/package/", "path/to/a/module.py"],
            description_style="full",
            fix_me="FIX THIS",
        )

    silenced_errors, not_silenced_errors, messages = result

## Recommended Mypy Flags

To enable all checks utilized by `mypy-upgrade` to silence as many errors as possible, the
following flags should be set when creating the type checking report to pass to `mypy-upgrade`:

* `--show-absolute-path`

    * Required if running `mypy-upgrade` in a separate directory than `mypy`

* `--strict`

    * Enables `mypy-upgrade` to silence all possible mypy errors
    (see [Known Limitations](#known-limitations) for exceptions)

* `--show-error-codes`

    * Ensures that error-code specific comments are added instead of blanket `type: ignore`
    comments

* `--warn-unused-ignores`

    * Ensures that unused `type: ignore` comments are removed

* `ignore-without-code`

    * When used with `--show-error-codes`, permits `mypy-upgrade` to replace existing
    `type: ignore` comments with code-specific `type: ignore` comments (enable from the
    command line with the `mypy` option `--enable-error-code`)

## Quick Start

`mypy-upgrade` can be installed via `pip`.

    python3 -m pip install mypy-upgrade

If you want to run the latest version of the code, you can install from the
repo directly:

    python3 -m pip install -U git+https://github.com/ugognw/mypy-upgrade.git@development
    # or if you don't have 'git' installed
    python3 -m pip install -U https://github.com/ugognw/mypy-upgrade/tree/development

## Known Limitations

The following limitations derive mainly from Python syntax issues and are unable to be handled
by `mypy-upgrade`. If you can't resolve the error directly, please consider refactoring to permit
error suppression.

* Type errors on lines ending in line continuation characters or within multiline f-strings

    * Comments are not permitted within multiline strings or following line continuation characters
    and Mypy only recognizes inline `type: ignore` comments (see
    [#3448](https://github.com/python/mypy/issues/3448))

    * Pre-formatting your code with a PEP8 adherent formatter
    (e.g., [`black`](http://black.readthedocs.io)) to replace such lines with parentheses is
    recommended.

* Improperly specified type hints within comments

    * `mypy` will report a type error if a type hint is improperly specified;
    for example, given the following code:

            x = {}  # type: set

    `mypy` will produce a `type-arg` error in column 1 and `mypy-upgrade` will
    place a `# type: ignore[type-arg]` comment at the end, which will, in turn,
    negate the effectiveness of the `# type: set` commment and eliminate the
    need for the `# type: ignore[type-arg]` comment

* `mypy` `"syntax"` errors are not silenced

    * It is recommended that you fix your code such that it is syntactically valid prior to using `mypy-upgrade`

## Similar Projects

If this doesn't fit your use-case, maybe one of these other projects will!

* [`geo7/mypy_clean_slate`](https://github.com/geo7/mypy_clean_slate/tree/main): `mypy`
reports are generated internally in `--strict` mode; includes
support for suppressing multiple errors on a single line; an inspiration for
much of `mypy-upgrade`'s implementation

* [`whtsky/mypy-silent`](https://github.com/whtsky/mypy-silent/tree/master):
relies solely on [`typer`](https://typer.tiangolo.com) + the standard
library; includes support for removing unused `type: ignore` comments but no
support for suppressing multiple errors on a single line; another inspiration
for much of `mypy-upgrade`'s implementation

* [`patrick91/mypy-silent`](https://github.com/patrick91/mypy-silent/tree/feature/multiple-errors): a
fork of `whtsky/mypy-silent` with support for
suppressing multiple errors on a single line (on the `feature/multiple-errors` branch)

* [`uptickmetachu/mypy-silent`](https://github.com/uptickmetachu/mypy-silent/tree/main): a fork
of `whtsky/mypy-silent` with support for suppressing multiple errors on a single line
