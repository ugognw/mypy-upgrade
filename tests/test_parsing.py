# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import re
import typing
from itertools import combinations, product

import pytest

from mypy_upgrade.parsing import MypyError, description_to_type_ignore


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
    def test_should_strip_whitespace_from_description(
        parsed_errors: list[MypyError],
    ) -> None:
        assert (e.description.strip() == e.description for e in parsed_errors)

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
        for filename, line_number, *_ in parsed_errors:
            if group_filename == filename:
                increasing_within_group.append(line_number >= last_line_number)
            else:
                group_filename = filename

            last_line_number = line_number

        assert all(increasing_within_group)


DESCRIPTION_STUBS = [
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


class TestDescriptionToTypeIgnore:
    @staticmethod
    @pytest.mark.parametrize("stub", DESCRIPTION_STUBS)
    def test_should_return_empty_tuple_with_no_error_code(stub: str) -> None:
        description = stub.replace("<placeholder>", "")
        assert description_to_type_ignore(description) == ()

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_code"), product(DESCRIPTION_STUBS, ERROR_CODES[1:3])
    )
    def test_should_return_error_code_string_with_one_error_code(
        stub: str, error_code: str
    ) -> None:
        description = stub.replace("<placeholder>", f"[{error_code}]")
        assert description_to_type_ignore(description) == (error_code,)

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(DESCRIPTION_STUBS, combinations(ERROR_CODES[1:4], 2)),
    )
    def test_should_return_error_code_string_with_two_error_code(
        stub: str, error_codes: tuple[str, str]
    ) -> None:
        description = stub.replace(
            "<placeholder>", f"[{', '.join(error_codes)}]"
        )
        assert description_to_type_ignore(description) == error_codes

    @staticmethod
    @pytest.mark.parametrize(
        ("stub", "error_codes"),
        product(DESCRIPTION_STUBS, combinations(ERROR_CODES[-4:], 3)),
    )
    def test_should_return_error_code_string_with_three_error_codes(
        stub: str, error_codes: tuple[str, str, str]
    ) -> None:
        description = stub.replace(
            "<placeholder>", f"[{', '.join(error_codes)}]"
        )
        assert description_to_type_ignore(description) == error_codes
