from __future__ import annotations

import pytest

from mypy_upgrade.editing import add_type_ignore_comment

TYPE_IGNORE_STUBS = [
    "",
    "type: ignore[<error-code>]",
    "type: ignore[<error-code>, <error-code>]",
]

COMMENT_SUFFIXES = ["", "# noqa", " comment"]

ERROR_CODES = [
    "arg-type",
    "attr-defined",
    "no-untyped-def",
    "override",
    "type-arg",
    "union-attr",
]


@pytest.fixture(name="type_ignore_stub", params=TYPE_IGNORE_STUBS)
def fixture_type_ignore_stub(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(name="comment_suffix", params=COMMENT_SUFFIXES)
def fixture_comment_suffix(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(name="initial_error_codes")
def fixture_initial_error_codes(type_ignore_stub: str) -> list[str]:
    num_of_initial_error_codes = type_ignore_stub.count("<error-code>")
    return ERROR_CODES[:num_of_initial_error_codes]


@pytest.fixture(name="type_ignore_comment")
def fixture_type_ignore_comment(
    type_ignore_stub: str, initial_error_codes: str
) -> str:
    type_ignore_comment = type_ignore_stub
    for code in initial_error_codes:
        type_ignore_comment = type_ignore_stub.replace("<error-code>", code, 1)

    return type_ignore_comment


@pytest.fixture(name="comment")
def fixture_comment(type_ignore_comment: str, comment_suffix: str) -> str:
    return type_ignore_comment + comment_suffix


@pytest.fixture(name="final_comment")
def fixture_final_comment(comment: str) -> str:
    return add_type_ignore_comment(comment, ERROR_CODES)


def test_should_retain_existing_error_codes(
    final_comment: str,
    initial_error_codes: list[str],
) -> None:
    assert all(e in final_comment for e in initial_error_codes)


def test_should_add_new_error_codes(final_comment: str) -> None:
    assert all(code in final_comment for code in ERROR_CODES)


def test_should_preserve_existing_comment(
    final_comment: str, comment_suffix: str
) -> None:
    assert comment_suffix.lstrip("# ") in final_comment


def test_should_place_type_ignore_comment_first(final_comment: str) -> None:
    assert final_comment.startswith("# type: ignore")


def test_should_sort_error_codes(final_comment: str) -> None:
    sorted_error_codes = sorted(ERROR_CODES)
    indices = [
        final_comment.index(error_code) for error_code in sorted_error_codes
    ]
    assert indices == sorted(indices)


def test_should_not_add_duplicate_error_codes(final_comment: str) -> None:
    assert all(final_comment.count(error_code) for error_code in ERROR_CODES)
