from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import MypyError, string_to_error_codes
from mypy_upgrade.silence import create_suppression_comment

TYPE_IGNORE_COMMENTS = ["", "# type: ignore", "# type: ignore[assignment]"]

COMMENT_SUFFIXES = ["", "# noqa", "# description with 'type: ignore' comment"]


@pytest.fixture(
    name="type_ignore_comment", params=TYPE_IGNORE_COMMENTS, scope="class"
)
def fixture_type_ignore_comment(request: pytest.FixtureRequest) -> str:
    code_snippet: str = request.param
    return code_snippet


@pytest.fixture(name="comment_suffix", params=COMMENT_SUFFIXES, scope="class")
def fixture_comment_suffix(request: pytest.FixtureRequest) -> str:
    comment_suffix: str = request.param
    return comment_suffix


@pytest.fixture(name="comment", scope="class")
def fixture_comment(type_ignore_comment: str, comment_suffix: str) -> str:
    return f"{type_ignore_comment} {comment_suffix}".strip()


@pytest.fixture(
    name="description_style", params=("full", "none"), scope="class"
)
def fixture_description_style(request: pytest.FixtureRequest) -> str:
    description_style: str = request.param
    return description_style


@pytest.fixture(
    name="fix_me", params=("THIS NEEDS TO BE FIXED", " "), scope="class"
)
def fixture_fix_me(request: pytest.FixtureRequest) -> str:
    fix_me: str = request.param
    return fix_me.strip()


@pytest.fixture(name="suppression_comment")
def fixture_suppression_comment(
    comment: str,
    errors: list[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> str:
    suppression_comment: str = create_suppression_comment(
        comment, iter(errors), description_style, fix_me
    )
    return suppression_comment


class TestCreateSuppressionComment:
    @staticmethod
    def test_should_not_add_duplicate_error_codes(
        suppression_comment: str, errors_to_add: list[MypyError]
    ) -> None:
        added_errors = string_to_error_codes(suppression_comment)
        assert not any(
            added_errors.count(error.error_code) > 1 for error in errors_to_add
        )

    @staticmethod
    def test_should_place_all_non_unused_ignore_errors_in_comment(
        suppression_comment: str, errors_to_add: list[MypyError]
    ) -> None:
        assert all(
            error.error_code in suppression_comment for error in errors_to_add
        )

    @staticmethod
    def test_should_place_type_ignore_at_beginning_of_comment(
        suppression_comment: str,
    ) -> None:
        comment_start = suppression_comment.find("#")
        if comment_start > -1:
            assert suppression_comment.startswith("# type: ignore")

    @staticmethod
    def test_should_trim_whitespace(
        suppression_comment: str,
    ) -> None:
        assert suppression_comment.strip() == suppression_comment

    @staticmethod
    def test_should_preserve_existing_suffix(
        suppression_comment: str, comment_suffix: str
    ) -> None:
        assert comment_suffix.strip() in suppression_comment

    @staticmethod
    def test_should_add_description_respecting_description_style(
        suppression_comment: str,
        description_style: str,
        errors_to_add: list[MypyError],
    ) -> None:
        if description_style == "full":
            assert all(
                error.message in suppression_comment for error in errors_to_add
            )
        else:
            assert not any(
                error.message in suppression_comment for error in errors_to_add
            )

    @staticmethod
    def test_should_add_fix_me(suppression_comment: str, fix_me: str) -> None:
        if fix_me.strip():
            assert fix_me in suppression_comment
        else:
            assert "FIX ME" not in suppression_comment

    @staticmethod
    def test_should_not_add_ignore_without_code(
        suppression_comment: str,
    ) -> None:
        assert "ignore-without-code" not in suppression_comment

    @staticmethod
    def test_should_replace_existing_type_ignore_when_ignoring_without_code(
        suppression_comment: str,
    ) -> None:
        assert not suppression_comment.count("# type: ignore") > 1

    @staticmethod
    def test_should_add_mypy_suggested_codes_from_ignore_without_code(
        suppression_comment: str, ignore_without_code_error: MypyError
    ) -> None:
        suggested_codes = string_to_error_codes(
            ignore_without_code_error.message
        )
        if suggested_codes:
            assert all(code in suppression_comment for code in suggested_codes)
