# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import pytest

from mypy_upgrade.parsing import MypyError, string_to_error_codes
from mypy_upgrade.silence import _extract_error_details


@pytest.fixture(name="error_details", scope="class")
def fixture_error_details(
    errors: list[MypyError],
) -> tuple[list[str], list[str], list[str]]:
    return _extract_error_details(errors=errors)


class TestExtractErrorDetails:
    @staticmethod
    def test_should_return_all_nonunused_ignore_without_code_as_codes_to_add(
        errors_to_add: list[MypyError],
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        assert all(
            code.error_code in error_details[0] for code in errors_to_add
        )

    @staticmethod
    def test_should_return_unused_ignore_errors_as_codes_to_remove(
        unused_ignore_error: MypyError,
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        to_remove = string_to_error_codes(string=unused_ignore_error.message)
        if to_remove:
            assert to_remove[0] in error_details[2]
        else:
            assert "*" in error_details[2]

    @staticmethod
    def test_should_return_asterisk_as_codes_to_remove_if_no_suggested_codes_for_ignore_without_code_error(  # noqa: E501
        ignore_without_code_error: MypyError,
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        to_add = string_to_error_codes(
            string=ignore_without_code_error.message
        )
        if not to_add:
            assert "*" in error_details[2]

    @staticmethod
    def test_should_not_return_without_code_errors(
        error_details: tuple[list[str], list[str], MypyError | None, bool]
    ) -> None:
        assert not any(
            code == "ignore-without-code" for code in error_details[0]
        )

    @staticmethod
    def test_should_return_suggested_error_codes_as_codes_to_add(
        ignore_without_code_error: MypyError,
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        to_add = string_to_error_codes(
            string=ignore_without_code_error.message
        )
        if to_add:
            assert all(code in error_details[0] for code in to_add)

    @staticmethod
    def test_should_return_descriptions_of_used_ignore_without_code_errors(
        error_details: tuple[list[str], list[str], list[str]],
        errors_to_add: list[MypyError],
    ) -> None:
        descriptions = error_details[1]
        assert all(error.message in descriptions for error in errors_to_add)

    @staticmethod
    def test_should_not_return_descriptions_of_unused_ignore_errors(
        unused_ignore_error: MypyError,
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        descriptions = error_details[1]
        assert not any(
            description == unused_ignore_error.message
            for description in descriptions
        )

    @staticmethod
    def test_should_not_return_descriptions_of_without_code_errors(
        ignore_without_code_error: MypyError,
        error_details: tuple[list[str], list[str], list[str]],
    ) -> None:
        descriptions = error_details[1]
        assert not any(
            description == ignore_without_code_error.message
            for description in descriptions
        )
