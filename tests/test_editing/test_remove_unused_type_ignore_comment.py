from __future__ import annotations

import re
from collections.abc import Iterable
from itertools import combinations

import pytest

from mypy_upgrade.editing import remove_unused_type_ignore_comments

ERROR_CODES = [
    "",
    "override",
    "arg-type",
    "attr-defined",
]

CODE_COMBINATIONS = (
    [[e] for e in ERROR_CODES]
    + list(combinations(ERROR_CODES[1:], r=2))
    + [ERROR_CODES[1:]]
)


COMMENT_SUFFIXES = [
    "",
    "# noqa",
]


class TestAllCombinations:
    @staticmethod
    @pytest.fixture(
        name="error_codes", scope="class", params=CODE_COMBINATIONS
    )
    def fixture_error_codes(request: pytest.FixtureRequest) -> str:
        comment_suffix: str = request.param
        return comment_suffix

    @staticmethod
    @pytest.fixture(
        name="codes_to_remove", scope="class", params=CODE_COMBINATIONS
    )
    def fixture_codes_to_remove(request: pytest.FixtureRequest) -> str:
        comment_suffix: str = request.param
        return comment_suffix

    @staticmethod
    @pytest.fixture(name="stub", scope="class")
    def fixture_stub(error_codes: list[str]) -> str:
        return f'# type: ignore[{", ".join(error_codes)}]'

    @staticmethod
    @pytest.fixture(
        name="comment_suffix", scope="class", params=COMMENT_SUFFIXES
    )
    def fixture_comment_suffix(request: pytest.FixtureRequest) -> str:
        comment_suffix: str = request.param
        return comment_suffix

    @staticmethod
    @pytest.fixture(name="comment", scope="class")
    def fixture_comment(stub: str, comment_suffix: str) -> str:
        return f"{stub} {comment_suffix}"

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
