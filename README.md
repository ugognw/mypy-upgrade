# mypy-upgrade

[![PyPI - Version](https://img.shields.io/pypi/v/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mypy-upgrade.svg)](https://pypi.org/project/mypy-upgrade)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install mypy-upgrade
```

## License

`mypy-upgrade` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Usage

"Pyre-like" invocation
```console
mypy -p ase | mypy-upgrade -p ase
```

Save the mypy report in a file
```console
mypy -p ase > mypy_report.txt
```

Pass the file to `mypy-upgrade`
```console
mypy-upgrade -p ase --report mypy_report.txt
```

For more info
```console
mypy-upgrade --help
```
