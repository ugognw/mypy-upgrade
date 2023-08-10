# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import re
import typing
from itertools import combinations, product

import pytest

from mypy_upgrade.parsing import MypyError, message_to_error_code


class TestParseReport:
    @staticmethod
    def test_should_return_as_many_entries_as_errors(
        parsed_errors: list[MypyError], report: typing.TextIO
    ) -> None:
        summary = report.readlines()[-1]

        match = re.search(r"Found (?P<num_errors>\d+) errors", summary)
        assert match is not None
        num_errors = int(match.group("num_errors"))
        assert num_errors == len(parsed_errors)

    @staticmethod
    def test_should_only_return_mypyerrors(
        parsed_errors: list[MypyError],
    ) -> None:
        assert all(isinstance(e, MypyError) for e in parsed_errors)

    @staticmethod
    def test_should_convert_line_number_to_integer(
        parsed_errors: list[MypyError],
    ) -> None:
        assert all(isinstance(e.line_no, int) for e in parsed_errors)

    @staticmethod
    def test_should_strip_whitespace_from_message(
        parsed_errors: list[MypyError],
    ) -> None:
        assert (e.message.strip() == e.message for e in parsed_errors)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_filename_first(
        parsed_errors: list[MypyError],
    ) -> None:
        filenames = [e.filename for e in parsed_errors]
        assert filenames == sorted(filenames)

    @staticmethod
    def test_should_sort_mypyerrors_with_respect_to_line_number_second(
        parsed_errors: list[MypyError],
    ) -> None:
        group_filename = None
        last_line_number = 0
        increasing_within_group = []
        for error in parsed_errors:
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


class TestMessageToErrorCode:
    @staticmethod
    @pytest.mark.parametrize("stub", MESSAGE_STUBS)
    def test_should_return_empty_tuple_with_no_error_code(stub: str) -> None:
        message = stub.replace("<placeholder>", "")
        assert message_to_error_code(message) == ()

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_code"), product(MESSAGE_STUBS, ERROR_CODES[1:3])
    )
    def test_should_return_error_code_string_with_one_error_code(
        stub: str, error_code: str
    ) -> None:
        message = stub.replace("<placeholder>", f"[{error_code}]")
        assert message_to_error_code(message) == (error_code,)

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(MESSAGE_STUBS, combinations(ERROR_CODES[1:4], 2)),
    )
    def test_should_return_error_code_string_with_two_error_code(
        stub: str, error_codes: tuple[str, str]
    ) -> None:
        message = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        assert message_to_error_code(message) == error_codes

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(MESSAGE_STUBS, combinations(ERROR_CODES[-4:], 3)),
    )
    def test_should_return_error_code_string_with_three_error_codes(
        stub: str, error_codes: tuple[str, str, str]
    ) -> None:
        message = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        assert message_to_error_code(message) == error_codes
