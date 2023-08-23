from __future__ import annotations

import re
from collections.abc import Collection

import pytest

from mypy_upgrade.editing import remove_unused_type_ignore_comments


class TestAllCombinations:
    @staticmethod
    @pytest.fixture(name="remove_result", scope="class")
    def fixture_remove_result(comment: str, codes_to_remove: list[str]) -> str:
        return remove_unused_type_ignore_comments(comment, codes_to_remove)

    @staticmethod
    def test_should_remove_all_error_codes_if_asterisk_in_codes_to_remove(
        comment: str, error_codes: Collection[str]
    ) -> None:
        result = remove_unused_type_ignore_comments(comment, error_codes)
        assert not any(code in result for code in error_codes if code)

    @staticmethod
    def test_should_only_remove_code_in_type_ignore_comment(
        stub: str,
        error_codes: Collection[str],
    ) -> None:
        comment = f"{stub} # don't remove {error_codes!s}"
        result = remove_unused_type_ignore_comments(comment, error_codes)
        stripped_result = re.sub(r"type: ignore\[[a-z, \-]\]", "", result)
        assert str(error_codes) in stripped_result

    @staticmethod
    def test_should_only_remove_codes_to_remove(
        remove_result: str,
        error_codes: Collection[str],
        codes_to_remove: Collection[str],
    ) -> None:
        assert all(
            code in remove_result
            for code in error_codes
            if code not in codes_to_remove
        )

    @staticmethod
    def test_should_remove_all_codes_to_remove(
        remove_result: str,
        codes_to_remove: Collection[str],
    ) -> None:
        assert not any(
            code in remove_result for code in codes_to_remove if code
        )

    @staticmethod
    def test_should_preserve_non_type_ignore_comment(
        remove_result: str,
        comment_suffix: str,
    ) -> None:
        assert comment_suffix in remove_result

    @staticmethod
    def test_should_not_change_comment_without_type_ignore_comment(
        comment_suffix: str, codes_to_remove: list[str]
    ) -> None:
        result = remove_unused_type_ignore_comments(
            comment_suffix, codes_to_remove
        )
        assert result == comment_suffix

    @staticmethod
    def test_should_remove_type_ignore_comment_if_all_codes_in_comment_in_codes_to_remove(  # noqa: E501
        comment: str,
        error_codes: Collection[str],
    ) -> None:
        if any(code for code in error_codes):
            result = remove_unused_type_ignore_comments(
                comment=comment, codes_to_remove=error_codes
            )
            assert not result.startswith("# type: ignore")
