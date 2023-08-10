from __future__ import annotations

from itertools import combinations, product

import pytest

from mypy_upgrade.editing import remove_unused_type_ignore_comment

DESCRIPTION_STUBS = [
    'Unused "type: ignore<placeholder>" comment',
    "Unused 'type: ignore<placeholder>' comment",
]

ERROR_CODES = [
    "",
    "override",
    "arg-type",
    "attr-defined",
]

COMMENT_SUFFIXES = [
    "\n",
    "type: ignore\n",
    "# noqa\n",
]


@pytest.mark.parametrize(
    ("stub", "error_code", "comment_suffix"),
    product(DESCRIPTION_STUBS, ERROR_CODES[1:3], COMMENT_SUFFIXES),
)
def test_should_remove_specified_error_codes1(
    stub: str, error_code: str, comment_suffix: str
) -> None:
    comment = stub.replace("<placeholder>", f"[{error_code}]") + comment_suffix
    result = remove_unused_type_ignore_comment(comment, [error_code])
    assert error_code not in result


@pytest.mark.parametrize(
    ("stub", "error_codes", "comment_suffix"),
    product(
        DESCRIPTION_STUBS,
        combinations(ERROR_CODES[1:3], 2),
        COMMENT_SUFFIXES,
    ),
)
def test_should_remove_specified_error_codes2(
    stub: str,
    error_codes: tuple[str, str],
    comment_suffix: str,
) -> None:
    comment = (
        stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        + comment_suffix
    )
    result = remove_unused_type_ignore_comment(comment, error_codes)
    assert not any(error in result for error in error_codes)


@pytest.mark.parametrize(
    ("stub", "comment_suffix", "error_code"),
    product(DESCRIPTION_STUBS, COMMENT_SUFFIXES, ERROR_CODES),
)
def test_should_remove_whole_type_ignore_comment_if_no_code_specified(
    stub: str,
    comment_suffix: str,
    error_code: str,
) -> None:
    type_ignore = stub.replace("<placeholder>", error_code)
    comment = type_ignore + comment_suffix
    result = remove_unused_type_ignore_comment(comment, ())
    assert type_ignore not in result
