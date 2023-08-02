from itertools import combinations, product

import pytest

from mypy_upgrade.parsing import description_to_type_ignore

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


@pytest.mark.parametrize("stub", DESCRIPTION_STUBS)
def test_should_return_empty_tuple_with_no_error_code(stub: str):
    description = stub.replace("<placeholder>", "")
    assert description_to_type_ignore(description) == ()


@pytest.mark.parametrize(
    ("stub", "error_code"), product(DESCRIPTION_STUBS, ERROR_CODES[1:3])
)
def test_should_return_error_code_string_with_one_error_code(
    stub: str, error_code: str
):
    description = stub.replace("<placeholder>", f"[{error_code}]")
    assert description_to_type_ignore(description) == (error_code,)


@pytest.mark.parametrize(
    ("stub", "error_codes"),
    product(DESCRIPTION_STUBS, combinations(ERROR_CODES[1:4], 2)),
)
def test_should_return_error_code_string_with_two_error_code(
    stub: str, error_codes: tuple[str, str]
):
    description = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
    assert description_to_type_ignore(description) == error_codes


@pytest.mark.parametrize(
    ("stub", "error_codes"),
    product(DESCRIPTION_STUBS, combinations(ERROR_CODES[-4:], 3)),
)
def test_should_return_error_code_string_with_three_error_codes(
    stub: str, error_codes: tuple[str, str, str]
):
    description = stub.replace("<placeholder>", f"[{', '.join(error_codes)}]")
    assert description_to_type_ignore(description) == error_codes
