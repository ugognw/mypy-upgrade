from __future__ import annotations

import re
from itertools import permutations, product

import pytest

from mypy_upgrade.editing import format_type_ignore_comment

SINGLE_CODE_DANGLING_COMMA_COMMENT_STUBS = [
    # Type ignore comments with 1 error code
    "type: ignore[, <error-code>]",
    "type: ignore[<error-code>, , ]",
    "type: ignore[, <error-code>, ]",
]

DUAL_CODE_DANGLING_COMMA_COMMENT_STUBS = [
    # Type ignore comments with 2 error codes
    "type: ignore[, , <error-code-1>, <error-code-2>]",
    "type: ignore[, <error-code-1>, <error-code-2>, ]",
    "type: ignore[,<error-code-1>,,<error-code-2>,]",
]

NO_ERROR_CODE_TYPE_IGNORES = [
    "type: ignore",
    "type: ignore[]",
    "type: ignore[,]",
    "type: ignore[ , , ]",
]

ERROR_CODES = [
    "override",
    "type-arg",
    "no-untyped-def",
]

COMMENT_SUFFIXES = [
    "# noqa",
    "I'm supposed to be here",
    "# I'm supposed to be here",
]

TYPE_IGNORE_FORMAT_RE = re.compile(r"type: ignore\[[a-z\-]+(, [a-z\-]+)*\]")
RESIDUAL_COMMENT_RE = re.compile(r"(#.+\S)?")


@pytest.mark.parametrize(
    ("type_ignore_stub", "error_code"),
    product(SINGLE_CODE_DANGLING_COMMA_COMMENT_STUBS, ERROR_CODES),
)
def test_should_remove_dangling_commas1(
    type_ignore_stub: str, error_code: str
) -> None:
    type_ignore_comment = type_ignore_stub.replace("<error-code>", error_code)
    formatted_type_ignore = format_type_ignore_comment(type_ignore_comment)
    assert TYPE_IGNORE_FORMAT_RE.match(formatted_type_ignore)


@pytest.mark.parametrize(
    ("type_ignore_stub", "error_codes"),
    product(
        DUAL_CODE_DANGLING_COMMA_COMMENT_STUBS, permutations(ERROR_CODES, 2)
    ),
)
def test_should_remove_dangling_commas2(
    type_ignore_stub: str, error_codes: tuple[str, str]
) -> None:
    error_code1, error_code2 = error_codes
    type_ignore_comment = type_ignore_stub.replace(
        "<error-code-1>", error_code1
    )
    type_ignore_comment = type_ignore_comment.replace(
        "<error-code-2>", error_code2
    )
    formatted_type_ignore = format_type_ignore_comment(type_ignore_comment)
    assert TYPE_IGNORE_FORMAT_RE.match(formatted_type_ignore)


@pytest.mark.parametrize("type_ignore_comment", NO_ERROR_CODE_TYPE_IGNORES)
def test_should_remove_type_ignore_without_error_codes(
    type_ignore_comment: str,
) -> None:
    assert format_type_ignore_comment(type_ignore_comment) == ""


@pytest.mark.parametrize("type_ignore_stub", NO_ERROR_CODE_TYPE_IGNORES)
def test_should_remove_trailing_whitespace(
    type_ignore_stub: str,
) -> None:
    assert format_type_ignore_comment(type_ignore_stub + " ") == ""


@pytest.mark.parametrize(
    ("type_ignore_stub", "comment_suffix"),
    product(NO_ERROR_CODE_TYPE_IGNORES, COMMENT_SUFFIXES),
)
def test_should_preserve_existing_comment(
    type_ignore_stub: str, comment_suffix: str
) -> None:
    formatted_type_ignore_comment = format_type_ignore_comment(
        type_ignore_stub + comment_suffix
    )
    assert comment_suffix.strip() in formatted_type_ignore_comment


@pytest.mark.parametrize(
    ("type_ignore_stub", "comment_suffix"),
    product(NO_ERROR_CODE_TYPE_IGNORES, COMMENT_SUFFIXES),
)
def test_should_preserve_existing_comment_without_surrounding_whitespace(
    type_ignore_stub: str, comment_suffix: str
) -> None:
    formatted_type_ignore_comment = format_type_ignore_comment(
        type_ignore_stub + comment_suffix
    )
    assert RESIDUAL_COMMENT_RE.match(formatted_type_ignore_comment)


@pytest.mark.parametrize(
    ("type_ignore_stub", "comment_suffix"),
    product(NO_ERROR_CODE_TYPE_IGNORES, COMMENT_SUFFIXES),
)
def test_should_trim_repeating_comment_characters(
    type_ignore_stub: str, comment_suffix: str
) -> None:
    formatted_type_ignore_comment = format_type_ignore_comment(
        type_ignore_stub + comment_suffix
    )
    assert not formatted_type_ignore_comment.startswith("##")
