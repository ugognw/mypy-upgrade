from __future__ import annotations

import pytest

from mypy_upgrade.editing import add_type_ignore_comment

ERROR_CODES = [
    "arg-type",
    "attr-defined",
    "no-untyped-def",
    "override",
]


class TestAllCombinations:
    @staticmethod
    @pytest.fixture(name="final_comment", scope="class")
    def fixture_final_comment(comment: str) -> str:
        type_ignore_comment: str = add_type_ignore_comment(
            comment, ERROR_CODES
        )
        return type_ignore_comment

    @staticmethod
    def test_should_retain_existing_error_codes(
        final_comment: str,
        error_codes: list[str],
    ) -> None:
        assert all(e in final_comment for e in error_codes)

    @staticmethod
    def test_should_add_new_error_codes(final_comment: str) -> None:
        assert all(code in final_comment for code in ERROR_CODES)

    @staticmethod
    def test_should_preserve_existing_comment(
        final_comment: str, comment_suffix: str
    ) -> None:
        assert comment_suffix.lstrip("# ") in final_comment

    @staticmethod
    def test_should_place_type_ignore_comment_first(
        final_comment: str,
    ) -> None:
        assert final_comment.startswith("# type: ignore")

    @staticmethod
    def test_should_sort_error_codes(
        final_comment: str, error_codes: list[str]
    ) -> None:
        sorted_error_codes = sorted(set(ERROR_CODES).union(error_codes))
        indices = [
            final_comment.index(error_code)
            for error_code in sorted_error_codes
        ]
        assert indices == sorted(indices)

    @staticmethod
    def test_should_not_add_duplicate_error_codes(final_comment: str) -> None:
        assert all(
            final_comment.count(error_code) for error_code in ERROR_CODES
        )

    @staticmethod
    def test_should_not_add_empty_error_codes(final_comment: str) -> None:
        assert "# type: ignore[]" not in final_comment
