# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

This project implements a version of
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) described
[here]((https://iscinumpy.dev/post/bound-version-constraints/#semver)) called
"Realistic" Semantic Versioning.

## [Unreleased]

### Added

* Recommended `mypy` flags in README

* `--fix-me` options for CLI and corresponding positional argument in `.main.mypy_upgrade`
and `.silence.silence_errors`

* `.parsing.parse_report` optionally supports parsing the start column and end
lines/columns in mypy type checking reports

* Sample mypy type checking reoprts for functional tests with column numbers

* `MypyError`s have `col_offset` as an additional field

* `utils.UnsilenceableRegion`: named tuple to represent line with line continuation
characters or lines encapsulated by multline strings.

* Functions

    * `.utils.find_safe_end_line`

    * `.utils.find_unsilenceable_regions`

* Unit tests

    * `.utils.find_safe_end_line`

    * `.utils.find_unsilenceable_regions`

    * `.utils.UnsilenceableRegion.surrounds`

* `.parsing.parse_mypy_report` optionally parses error line/column number start/end locations

### Changed

* `--with-descriptions` flag changed to `--description-style` option which accepts `full` or `none`
as values

* `suffix` parameter renamed to `description_style` in `.main.mypy_upgrade` and
`.silence.silence_errors`

* `MypyError.description` renamed to `MypyError.message`

* `.utils.def correct_line_numbers` returns `tuple[list[MypyError], list[MypyError]]` whose
first entry represents `MypyError`s that can be safely silenced and whose second entry
represents those `MypyError`s that cannot be safely silenced

* Unit tests

    * `.utils.correct_line_numbers`

        * changed to reflect new `MypyError` data model and return values for
        `correct_line_numbers`

    * `.silence`: added arguments for `col_offset` in `MypyError`

## [0.0.1-alpha.3] - 2023-08-04

### Added

* `__future__` imports for Python <3.10 support

* `typing-extensions` dependency for Python <3.8

* `mypy_upgrade.cli.mypy_upgrade` function which encapsulates application logic

* README

    * overview of features

    * preview of command-line options

    * known bugs

    * similar projects

* New modules:

    * `mypy_upgrade.editing`: comment editing functions

    * `mypy_upgrade.filter`: error filtering functions

    * `mypy_upgrade.parsing`: defines the `MypyError` named tuple and report parsing logic

    * `mypy_upgrade.silence`: suppress errors by add/removing comments

    * `mypy_upgrade.utils`: utilities for processing code text

* Testing

    * Group common data to fixtures in `conftest.py`

    * Functional tests on ASE codebase (with corresponding test data and test environment dependency)

    * Unit tests for:

        * `mypy_upgrade.cli._create_argument_parser`

        * `mypy_upgrade.editing.add_type_ignore_comment`

        * `mypy_upgrade.editing.format_type_ignore_comment`

        * `mypy_upgrade.editing.remove_unused_type_ignore`

        * `mypy_upgrade.filter.filter_mypy_errors`

        * `mypy_upgrade.filter.get_module_paths`

        * `mypy_upgrade.parsing.description_to_type_ignore`

        * `mypy_upgrade.parsing.parse_mypy_error_report`

        * `mypy_upgrade.silence.silence_errors`

        * `mypy_upgrade.utils.split_code_and_comment`

        * `mypy_upgrade.utils.correct_line_numbers`

    * Add pytest markers for slow tests and functional tests

### Changed

* `mypy_upgrade.cli`

    * `.parse_report` moved to `mypy_upgrade.parsing` module

    * `.get_module_paths` function moved to `mypy_upgrade.filter` module

    * `.select_errors` renamed to `filter_mypy_errors` and moved to `mypy_upgrade.filter` module

    * `.silence_error`

        * renamed to `silence_errors` moved to `mypy_upgrade.silence` module

        * now accepts `str`, `Iterable[MypyError]`, `Literal["description"] | None` as parameters

        * removes unused type error suppression comments

        * respects previously existing comments

    * `.main` application logic moved to `.mypy_upgrade`

* Error information is stored as named tuple (`MypyError`)

* syntax of README examples

* Default to silence all errors in type checking report

* Use tokenize to find existing comments

* Group errors to be silenced by file and line number

### Removed

* Pypy and Python 3.12+ classifiers

* `.cli.extract_old_error`

### Fixed

* Support for placing suppression errors on the end of multiline statements

## [0.0.1-alpha.2] - 2023-07-31

### Fixed

* `importlib.abc error` [(see Issue #2)](https://github.com/ugognw/mypy-upgrade/issues/2)

## [0.0.1-alpha.1] - 2023-07-31

* First release

[Unreleased]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.3...development
[0.0.1-alpha.3]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.2...release-0.0.1-alpha.3
[0.0.1-alpha.2]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.1...release-0.0.1-alpha.2
[0.0.1-alpha.1]: https://github.com/ugognw/mypy-upgrade/tree/release-0.0.1-alpha.1
