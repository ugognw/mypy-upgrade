# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

This project implements a version of
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) described
[here]((https://iscinumpy.dev/post/bound-version-constraints/#semver)) called
"Realistic" Semantic Versioning.

## [0.0.1-beta.6] - 2023-12-22

### Added

* `mypy_upgrade.logging`: logging/printing facilities

* `dry_run` keyword argument (and corresponding CLI option `--dry-run`)
added to `mypy_upgrade.silence.silence_errors_in_file`
and `mypy_upgrade.silence.silence_errors_in_report`

* `codes_to_silence` keyword argument (and corresponding CLI option
`-s/--silence-error`) added to `mypy_upgrade.silence.silence_errors_in_file`
and `mypy_upgrade.silence.silence_errors_in_report`

* `-q/--quiet` CLI option aliases for `--suppress-warnings`

* `-S/--summarize` CLI option: print optionally detailed summary

* `-c/--colours` CLI option: print coloured messages

### Changed

* Printing results:
    * Silenced and not silenced errors are printed out on-the-fly instead of
    all at the end
    * New format (see `mypy_upgrade.silence._log_silencing_results`)

* `mypy_upgrade.cli.print_results` -> `mypy_upgrade.cli.summarize_results`;
`options` keyword replaced with `verbosity`

* CLI arguments encapsulated in `mypy_upgrade.cli.Options` class

* Warning messages (e.g., `mypy_upgrade.warnings.MISSING_ERROR_CODES`)
have been moved to the module in which they are emitted

* `mypy_upgrade.silence.MypyUpgradeResult` is now a 2-tuple (`silenced`,
`not_silenced`); messages can be retrieved by adding a `logging.Handler`
to the appropriate logger (e.g., `mypy_upgrade.cli.logger`)

### Removed

* `mypy_upgrade.warnings`


## [0.0.1-beta.5] - 2023-08-24

### Added

* API logic added to `mypy_upgrade.silence` through `silence_errors_in_report`

* `mypy_upgrade.utils.CommentSplitLine`: represents a line split into code
and comment

* `mypy_upgrade.silence.silence_errors_in_file`: silences errors in a given
file

* `mypy_upgrade.silence.create_suppression_comment`: creates error suppression
comment

* new unit tests for `mypy_upgrade.editing.remove_unused_type_ignore_comments`

### Changed

* All arguments are now keyword only

* `mypy_upgrade.cli.main`

    * `FileNotFoundError` due to missing report file no longer caught

* `mypy_upgrade.editing.add_type_ignore_comment` no longer removes
`type: ignore` comments without codes

* `mypy_upgrade.editing.format_type_ignore_comment`

    * no longer remove bare `type: ignore` comments

* `mypy_upgrade.editing.remove_unused_type_ignore_comments`

    * accepts collections of strings for `codes_to_remove` argument

    * no longer remove all codes if `codes_to_remove` "falsey"

    * removes all codes in comment if `"*"` in `codes_to_remove` or all codes
    in comment in `codes_to_remove`

    * does not touch comment if no "truthy" elements in `codes_to_remove`
    or no codes in `type: ignore` part of comment

    * only removes codes in `type: ignore` part of comment

* `mypy_upgrade.filter.get_module_paths` is now a private function
(i.e., `_get_module_paths`)

* `mypy_upgrade.filter.filter_mypy_errors`

    * rename to `mypy_upgrade.filter.filter_by_source`

    * accepts keyword-only arguments

* `mypy_upgrade.main.mypy_upgrade`

    * moved to `mypy_upgrade.silence` along with related logic (e.g.,
    `MypyUpgradeResult`)

    * renamed to `silence_errors_in_report`

    * refactored by splitting into smaller functions (i.e.,
    `silence_errors_in_file`, `create_suppression_comment`)

    * accepts a `TextIO` instance for the `report` argument

    * respect existing whitespace in code lines

* `mypy_upgrade.parsing.string_to_error_codes`

    * return unique error codes

* `mypy_upgrade.parsing.parse_mypy_report`

    * resets input stream position after reading

* `mypy_upgrade.silence._extract_error_details` returns a 3-tuple of lists of
strings

    * the third element is a list of codes to remove

* `mypy_upgrade.utils.divide_errors`

    * moved to `mypy_upgrade.filter` module

    * renamed to `filter_by_silenceability`

    * accepts iterable of `MypyError` instances, sequence of strings,
    and an iterable of `TokenInfo` instances as arguments

    * returns a list of `MypyError` instances

    * accepts keyword-only arguments

* `mypy_upgrade.utils.find_safe_end_line`

    * moved to `mypy_upgrade.filter`

    * renamed to `_is_safe_to_silence`

    * returns boolean

    * indicates that an error on any non-terminal line of an
    `UnsilenceableRegion` is not safe to silence

    * accepts keyword-only arguments

* `mypy_upgrade.utils.find_unsilenceable_regions`

    * moved to `mypy_upgrade.filter`

    * made private (e.g., `_find_unsilenceable_regions`)

    * accepts `comments` as a sequence of strings

    * accepts keyword-only arguments

* `mypy_upgrade.utils.split_into_code_and_comment` now splits all lines of
source into code and comment

    * accepts string and iterable of `TokenInfo` instances as arguments

    * returns list of `CommentSplitLine` instances

* `mypy_upgrade.utils.UnsilenceableRegion`

    * moved to `mypy_upgrade.filter`

    * `start` and `end` implemented as integers instead of tuples of integers

### Fixed

* `mypy_upgrade.utils.find_unsilenceable_regions`

    * recognize f-strings as unique tokens in Python 3.12+

### Removed

* `mypy_upgrade.utils.get_lines_and_tokens`

## [0.0.1-beta.4] - 2023-08-16

### Added

* Do not silence mypy `syntax` errors

* `mypy_upgrade.utils.get_lines_and_tokens`

### Changed

* `mypy_upgrade.silence.silence_errors` accepts `python_code` and `comment`
arguments instead of `line` argument

* `mypy_upgrade.utils.find_unsilenceable_regions` accepts `tokens` and
`comments` arguments instead of `TextIO` argument

* `mypy_upgrade.utils.correct_line_numbers` accepts `unsilenceable_regions`
instead of `TextIO` argument

* Rename `mypy_upgrade.utils.correct_line_numbers` to
`mypy_upgrade.utils.divide_errors`

* `mypy_upgrade.filter.get_module_paths` raises a `NotImplementedError` for
built-in modules

* Improved test coverage

### Fixed

* Unable to identify comment within implicitly continued line
[(see Issue #10)](https://github.com/ugognw/mypy-upgrade/issues/10)

### Removed

* Support for silencing errors preceding same line multiline string
    (`mypy_upgrade.utils.find_safe_end_line` changed accordingly)

    * also fixes
    [(see Issue #9)](https://github.com/ugognw/mypy-upgrade/issues/9)

* `mypy_upgrade.utils.split_code_and_comment`

## [0.0.1-beta.3] - 2023-08-11

### Changed

* `mypy_upgrade.parsing.message_to_error_code` renamed to
`mypy_upgrade.parsing.string_to_error_codes` and now returns longest
comma-separated list of error codes in string

* `mypy_upgrade.silence.silence_errors` refactored

### Fixed

* `mypy_upgrade.silence.silence_errors` does not add "ignore-without-code"
to `type: ignore` comments but instead will add the mypy-suggested error code
to the comment

### Removed

* PyPy support

## [0.0.1-beta.2] - 2023-08-10

### Added

* `mypy_upgrade.filter.get_module_paths` now handles built-in and frozen
modules/packages explicitly

### Changed

* Link targets CHANGELOG headers

* Rename `mypy_upgrade.parsing.description_to_type_ignore` to
`mypy_upgrade.parsing.message_to_error_code`

* Refactored CI-only functional tests

    * CI must define `MYPY_UPGRADE_TARGET` and `MYPY_UPGRADE_TARGET_INSTALL_DIR`;
    no need to define `MYPY_REPORT`

    * tests run `mypy` using pytest fixtures

* Removed redundant unit tests

## [0.0.1-beta.1] - 2023-08-08

### Added

* Python 3.12+ support

* Add PyPy 3.7-3.10 support

* CI-only functional tests for CLI

### Changed

* `mypy_upgrade.editing.remove_unused_type_ignore` renamed to
`mypy_upgrade.editing.remove_unused_type_ignore_comment`

### Removed

* Functional tests under `test_cli.TestMypyUpgrade6269340a3`

* "functionalx" pytest marks

* `ase` test dependency

## [0.0.1-alpha.5] - 2023-08-08

### Added

* Print version with `-V/--version` flag

* Print warnings if:

    * there are errors which are not silenced

    * there are errors without error codes

    * the filenames reported in the mypy error report are not found

* `mypy_upgrade.cli.MypyUpgradeResult`

* `mypy_upgrade.warnings`: warning messages and message creation functions

* Three levels of verbosity are now supported for the CLI (0, 1, 2)

* Optional warning suppression

* Unit tests

    * `mypy.warnings.create_not_silenced_errors_warning`

### Changed

* The order of `MypyError.line_no` and `MypyError.col_offset` has been
switched

* `mypy_upgrade.cli.mypy_upgrade` returns `MypyUpgradeResult`

### Fixed

* Addition of duplicate error codes if there are duplicate error codes in the
mypy type checking report
[(see Issue #4)](https://github.com/ugognw/mypy-upgrade/issues/4)

### Removed

* `mypy_upgrade.utils.UnsilenceableRegion.surrounds` and corresponding unit
tests

## [0.0.1-alpha.4] - 2023-08-06

### Added

* Recommended `mypy` flags in README

* `--fix-me` options for CLI and corresponding positional argument in
`mypy_upgrade.cli.mypy_upgrade` and `mypy_upgrade.silence.silence_errors`

* `mypy_upgrade.parsing.parse_report` optionally supports parsing the start
column and end lines/columns in mypy type checking reports

* Sample mypy type checking reoprts for functional tests with column numbers

* `MypyError` has `col_offset` as an additional field

* `mypy_upgrade.utils.UnsilenceableRegion`: named tuple to represent line with
line continuation characters or lines encapsulated by multline strings.

* Functions

    * `mypy_upgrade.utils.find_safe_end_line`

    * `mypy_upgrade.utils.find_unsilenceable_regions`

* Unit tests

    * `mypy_upgrade.utils.find_safe_end_line`

    * `mypy_upgrade.utils.find_unsilenceable_regions`

    * `mypy_upgrade.utils.UnsilenceableRegion.surrounds`

* `mypy_upgrade.parsing.parse_mypy_report` optionally parses error line/column
number start/end locations

### Changed

* `--with-descriptions` flag changed to `--description-style` option which
accepts `full` or `none` as values

* `suffix` parameter renamed to `description_style` in
`mypy_upgrade.cli.mypy_upgrade` and `mypy_upgrade.silence.silence_errors`

* `MypyError.description` renamed to `MypyError.message`

* `mypy_upgrade.utils.correct_line_numbers` returns
`tuple[list[MypyError], list[MypyError]]` whose first entry represents errors
that can be safely silenced and whose second entry represents those errors
that cannot be safely silenced

* Unit tests

    * `mypy_upgrade.utils.correct_line_numbers`

        * changed to reflect new `MypyError` data model and return values for
        `correct_line_numbers`

    * `mypy_upgrade.silence`: added arguments for `col_offset` in `MypyError`

## [0.0.1-alpha.3] - 2023-08-04

### Added

* `__future__` imports for Python <3.10 support

* `typing-extensions` dependency for Python <3.8

* `mypy_upgrade.cli.mypy_upgrade` function which encapsulates application
logic

* README

    * overview of features

    * preview of command-line options

    * known bugs

    * similar projects

* New modules:

    * `mypy_upgrade.editing`: comment editing functions

    * `mypy_upgrade.filter`: error filtering functions

    * `mypy_upgrade.parsing`: defines the `MypyError` named tuple and report
    parsing logic

    * `mypy_upgrade.silence`: suppress errors by add/removing comments

    * `mypy_upgrade.utils`: utilities for processing code text

* Testing [(closes Issue #1)](https://github.com/ugognw/mypy-upgrade/issues/1)

    * Group common data to fixtures in `conftest.py`

    * Functional tests on ASE codebase (with corresponding test data and test
    environment dependency)

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

    * `.select_errors` renamed to `filter_mypy_errors` and moved to
    `mypy_upgrade.filter` module

    * `.silence_error`

        * renamed to `silence_errors` moved to `mypy_upgrade.silence` module

        * now accepts `str`, `Iterable[MypyError]`,
        `Literal["description"] | None` as parameters

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

* `mypy_upgrade.cli.extract_old_error`

### Fixed

* Support for placing suppression errors on the end of multiline statements
[(see Issue #3)](https://github.com/ugognw/mypy-upgrade/issues/3)

## [0.0.1-alpha.2] - 2023-07-31

### Fixed

* `importlib.abc error`
[(see Issue #2)](https://github.com/ugognw/mypy-upgrade/issues/2)

## [0.0.1-alpha.1] - 2023-07-31

* First release

[0.0.1-beta.5]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-beta.4...release-0.0.1-beta.5
[0.0.1-beta.4]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-beta.3...release-0.0.1-beta.4
[0.0.1-beta.3]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-beta.2...release-0.0.1-beta.3
[0.0.1-beta.2]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-beta.1...release-0.0.1-beta.2
[0.0.1-beta.1]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.5...release-0.0.1-beta.1
[0.0.1-alpha.5]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.4...release-0.0.1-alpha.5
[0.0.1-alpha.4]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.3...release-0.0.1-alpha.4
[0.0.1-alpha.3]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.2...release-0.0.1-alpha.3
[0.0.1-alpha.2]: https://github.com/ugognw/mypy-upgrade/compare/release-0.0.1-alpha.1...release-0.0.1-alpha.2
[0.0.1-alpha.1]: https://github.com/ugognw/mypy-upgrade/tree/release-0.0.1-alpha.1
