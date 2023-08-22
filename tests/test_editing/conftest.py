from itertools import combinations

import pytest

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


@pytest.fixture(name="error_codes", scope="class", params=CODE_COMBINATIONS)
def fixture_error_codes(request: pytest.FixtureRequest) -> list[str]:
    error_codes: list[str] = request.param
    return error_codes


@pytest.fixture(
    name="codes_to_remove", scope="class", params=CODE_COMBINATIONS
)
def fixture_codes_to_remove(request: pytest.FixtureRequest) -> list[str]:
    codes_to_remove: list[str] = request.param
    return codes_to_remove


@pytest.fixture(name="stub", scope="class")
def fixture_stub(error_codes: list[str]) -> str:
    return f'# type: ignore[{", ".join(error_codes)}]'


@pytest.fixture(name="comment_suffix", scope="class", params=COMMENT_SUFFIXES)
def fixture_comment_suffix(request: pytest.FixtureRequest) -> str:
    comment_suffix: str = request.param
    return comment_suffix


@pytest.fixture(name="comment", scope="class")
def fixture_comment(stub: str, comment_suffix: str) -> str:
    return f"{stub} {comment_suffix}"
