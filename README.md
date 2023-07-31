# mypy-upgrade

[![PyPI - Version](https://img.shields.io/pypi/v/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)

-----

**Table of Contents**

- [Basic Usage](#basic-usage)
- [Command-Line Options](#command-line-options)
- [Quick Start](#quick-start)

`mypy-upgrade` is a command-line utility that provides automatic error
suppression for `mypy` (analogous to `pyre-upgrade`).

Given a type checking report from [mypy](http://mypy.readthedocs.io/),
`mypy-upgrade` will silence the listed errors using error suppression
comments. For example, with the following output from mypy:

    ase/utils/plotting.py:13: error: Incompatible default for argument "filename" (default has type "None", argument has type "str") [assignment]

`mypy-upgrade` will place a `# type: ignore[assignment]` comment at the
end of line 13 in `ase/utils/plotting.py`. If error codes are not present in
the `mypy` report (e.g., the `hide-error-codes` flag is set when `mypy` was
invoked), then a non-specific `# type: ignore` comment will be added instead.

> :warning: **Warning:** `mypy-check` **must** be run in the same directory
> that `mypy` was run.*

## Basic Usage

There are two idioms for invocation. To silence all errors in a package, one
can:

1. invoke `mypy-upgrade` in a "Pyre-like" fashion

        mypy -p my_package | mypy-upgrade -p my_package

2. create a `mypy` type checking report text file

        mypy -p my_package > mypy_report.txt

    and then pass the file to `mypy-upgrade`

        mypy-upgrade --report mypy_report.txt -p my_package

> :memo: **Note:** To ensure desired behaviour, packages and modules must be
passed using their fully qualified names (e.g., `my_package.my_module`).

## Command-Line Options

You may want to include the error descriptions provided by `mypy` in the
suppression comments so that you can fix them later.

    mypy-upgrade --report mypy_report.txt -d -p MY_PACKAGE

Files and directories can also be passed as positional arguments:

    mypy-upgrade --report mypy_report.txt path/to/my_package/ path/to/another_package/

    mypy-upgrade --report mypy_report.txt path/to/a/module.py

For a full list of all options and their descriptions, run

    mypy-upgrade --help

## Quick Start

`mypy-upgrade` can be installed via `pip`.

    python3 -m pip install mypy-upgrade

If you want to run the latest version of the code, you can install from the
repo directly:

    python3 -m pip install -U git+https://github.com/ugognw/mypy-upgrade.git
    # or if you don't have 'git' installed
    python3 -m pip install -U https://github.com/ugognw/mypy-upgrade/tree/development
