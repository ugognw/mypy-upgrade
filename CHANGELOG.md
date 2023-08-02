# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

This project implements a version of
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) described
[here]((https://iscinumpy.dev/post/bound-version-constraints/#semver)) called
"Realistic" Semantic Versioning.

## [Unreleased](https://github.com/ugognw/mypy-upgrade/tree/development)

## Added

* Unit tests for:

    * `mypy_upgrade.cli._create_argument_parser`

    * `mypy_upgrade.filter.filter_mypy_errors`

    * `mypy_upgrade.filter.get_module_paths`

    * `mypy_upgrade.parsing.description_to_type_ignore`

    * `mypy_upgrade.parsing.parse_mypy_error_report`

    * `mypy_upgrade.utils.split_code_and_comment`

### Changed

* Major refactor into modules

* Default to silence all errors in type checking report

* Use tokenize to find existing comments

* Group errors by file and line number

## [0.0.1-alpha.2](https://github.com/ugognw/mypy-upgrade/tree/release-0.0.1-alpha.2)

### Fixed

* `importlib.abc error` [(see Issue #2)](https://github.com/ugognw/mypy-upgrade/issues/2)

## [0.0.1-alpha.1](https://github.com/ugognw/mypy-upgrade/tree/release-0.0.1-alpha.1)

* First release
