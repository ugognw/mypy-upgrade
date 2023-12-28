# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import re
import typing
from itertools import combinations, product

import pytest

from mypy_upgrade.parsing import MypyError, string_to_error_codes


class TestParseReport:
    @staticmethod
    def test_should_return_as_many_entries_as_errors(
        errors_to_filter: list[MypyError], report: typing.TextIO
    ) -> None:
        summary = report.readlines()[-1]

        match = re.search(r"Found (?P<num_errors>\d+) error", summary)
        assert match is not None
        num_errors = int(match.group("num_errors"))
        assert num_errors == len(errors_to_filter)

    @staticmethod
    def test_should_only_return_mypyerrors(
        errors_to_filter: list[MypyError],
    ) -> None:
        assert all(isinstance(e, MypyError) for e in errors_to_filter)

    @staticmethod
    def test_should_convert_line_number_to_integer(
        errors_to_filter: list[MypyError],
    ) -> None:
        assert all(isinstance(e.line_no, int) for e in errors_to_filter)

    @staticmethod
    def test_should_strip_whitespace_from_message(
        errors_to_filter: list[MypyError],
    ) -> None:
        assert (e.message.strip() == e.message for e in errors_to_filter)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_filename_first(
        errors_to_filter: list[MypyError],
    ) -> None:
        filenames = [e.filename for e in errors_to_filter]
        assert filenames == sorted(filenames)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_line_number_second(
        errors_to_filter: list[MypyError],
    ) -> None:
        group_filename = None
        last_line_number = 0
        increasing_within_group = []
        for error in errors_to_filter:
            if group_filename == error.filename:
                increasing_within_group.append(
                    error.line_no >= last_line_number
                )
            else:
                group_filename = error.filename

            last_line_number = error.line_no

        assert all(increasing_within_group)


MESSAGE_STUBS = [
    'Unused "type: ignore<placeholder>" comment',
    "Unused 'type: ignore<placeholder>' comment",
    'Unused "type :ignore<placeholder>" comment',
    "Unused 'type :ignore<placeholder>' comment",
    'Unused "type : ignore<placeholder>" comment',
    "Unused 'type : ignore<placeholder>' comment",
]

ERROR_CODES = [
    "",
    "arg-type",
    "attr-defined",
    "override",
    "no-untyped-def",
    "type-arg",
    "union-attr",
]


class TestStringToErrorCodes:
    @staticmethod
    @pytest.mark.parametrize("stub", MESSAGE_STUBS)
    def test_should_return_empty_tuple_with_no_error_code(stub: str) -> None:
        message = stub.replace("<placeholder>", "")
        assert string_to_error_codes(string=message) == ()

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_code"), product(MESSAGE_STUBS, ERROR_CODES[1:3])
    )
    def test_should_return_error_code_string_with_one_error_code(
        stub: str, error_code: str
    ) -> None:
        message = stub.replace("<placeholder>", f"[{error_code}]")
        assert string_to_error_codes(string=message) == (error_code,)

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(MESSAGE_STUBS, combinations(ERROR_CODES[1:4], 2)),
    )
    def test_should_return_error_code_string_with_two_error_code(
        stub: str, error_codes: tuple[str, str]
    ) -> None:
        message = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        assert sorted(string_to_error_codes(string=message)) == sorted(
            error_codes
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(MESSAGE_STUBS, combinations(ERROR_CODES[-4:], 3)),
    )
    def test_should_return_error_code_string_with_three_error_codes(
        stub: str, error_codes: tuple[str, str, str]
    ) -> None:
        message = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        assert sorted(string_to_error_codes(string=message)) == sorted(
            error_codes
        )
