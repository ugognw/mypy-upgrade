from itertools import combinations, product

import pytest

from mypy_upgrade.editing import remove_unused_type_ignore

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

COMMENT_SUFFIXES = [
    "",
    "\n",
    " # another comment\n",
    "type: ignore\n",
    "# noqa\n",
]


@pytest.mark.parametrize(
    ("stub", "error_code", "to_remove", "comment_suffix"),
    product(
        DESCRIPTION_STUBS, ERROR_CODES[1:3], ERROR_CODES[1:3], COMMENT_SUFFIXES
    ),
)
def test_should_remove_specified_error_codes1(
    stub: str, error_code: str, to_remove: str, comment_suffix: str
) -> None:
    comment = stub.replace("<placeholder>", f"[{error_code}]") + comment_suffix
    result = remove_unused_type_ignore(comment, to_remove)
    assert to_remove not in result


@pytest.mark.parametrize(
    ("stub", "error_codes", "to_remove", "comment_suffix"),
    product(
        DESCRIPTION_STUBS,
        combinations(ERROR_CODES[1:4], 2),
        ERROR_CODES[1:3],
        COMMENT_SUFFIXES,
    ),
)
def test_should_remove_specified_error_codes2(
    stub: str,
    error_codes: tuple[str, str],
    to_remove: str,
    comment_suffix: str,
) -> None:
    comment = (
        stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        + comment_suffix
    )
    result = remove_unused_type_ignore(comment, to_remove)
    assert to_remove not in result


@pytest.mark.parametrize(
    ("stub", "error_codes", "to_remove", "comment_suffix"),
    product(
        DESCRIPTION_STUBS,
        combinations(ERROR_CODES[1:4], 2),
        combinations(ERROR_CODES[1:4], 2),
        COMMENT_SUFFIXES,
    ),
)
def test_should_remove_specified_error_codes3(
    stub: str,
    error_codes: tuple[str, str],
    to_remove: tuple[str, str],
    comment_suffix: str,
) -> None:
    comment = (
        stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        + comment_suffix
    )
    result = remove_unused_type_ignore(comment, to_remove)
    assert all(code not in result for code in to_remove)


@pytest.mark.parametrize(
    ("stub", "error_codes", "to_remove", "comment_suffix"),
    product(
        DESCRIPTION_STUBS,
        combinations(ERROR_CODES[-4:], 2),
        combinations(ERROR_CODES[-4:], 2),
        COMMENT_SUFFIXES,
    ),
)
def test_should_remove_specified_error_codes4(
    stub: str,
    error_codes: tuple[str, str],
    to_remove: tuple[str, str],
    comment_suffix: str,
) -> None:
    comment = (
        stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
        + comment_suffix
    )
    result = remove_unused_type_ignore(comment, to_remove)
    assert all(code not in result for code in to_remove)


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
    result = remove_unused_type_ignore(comment, ())
    assert type_ignore not in result
