from __future__ import annotations

import re
from collections.abc import Iterable

import pytest

from mypy_upgrade.editing import remove_unused_type_ignore_comments


class TestAllCombinations:
    @staticmethod
    @pytest.fixture(name="remove_result", scope="class")
    def fixture_remove_result(comment: str, codes_to_remove: list[str]) -> str:
        return remove_unused_type_ignore_comments(comment, codes_to_remove)

    @staticmethod
    def test_should_remove_all_error_codes_if_asterisk_in_codes_to_remove(
        comment: str, error_codes: Iterable[str]
    ) -> None:
        result = remove_unused_type_ignore_comments(comment, error_codes)
        assert not any(code in result for code in error_codes if code)

    @staticmethod
    def test_should_only_remove_code_in_type_ignore_comment(
        stub: str,
        error_codes: Iterable[str],
    ):
        comment = f"{stub} # don't remove {error_codes!s}"
        result = remove_unused_type_ignore_comments(comment, error_codes)
        stripped_result = re.sub(r"type: ignore\[[a-z, \-]\]", "", result)
        assert str(error_codes) in stripped_result

    @staticmethod
    def test_should_only_remove_codes_to_remove(
        remove_result: str,
        error_codes: Iterable[str],
        codes_to_remove: Iterable[str],
    ) -> None:
        assert all(
            code in remove_result
            for code in error_codes
            if code not in codes_to_remove
        )

    @staticmethod
    def test_should_remove_all_codes_to_remove(
        remove_result: str,
        codes_to_remove: Iterable[str],
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
