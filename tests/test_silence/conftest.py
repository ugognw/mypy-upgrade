import pytest

from mypy_upgrade.parsing import MypyError


@pytest.fixture(name="errors_to_add", scope="class")
def fixture_errors_to_add() -> list[MypyError]:
    return [
        MypyError(
            "package1/subpackage1/module1.py",
            1,
            0,
            "Function is missing a return type annotation",
            "no-untyped-def",
        ),
        MypyError(
            "package3/subpackage3/module3.py",
            318,
            0,
            'Incompatible types in assignment (expression has type "None", '
            'variable has type "list[int]")',
            "assignment",
        ),
    ]


@pytest.fixture(
    name="ignore_without_code_error",
    scope="class",
    params=(
        MypyError(
            "package/subpackage1/module1.py",
            1,
            0,
            '"type: ignore" comment without error code (consider "type: '
            'ignore[operator, type-var]" instead)',
            "ignore-without-code",
        ),
        MypyError(
            "package2/subpackage2/module2.py",
            72,
            0,
            '"type: ignore" comment without error code',
            "ignore-without-code",
        ),
    ),
)
def fixture_ignore_without_code_error(
    request: pytest.FixtureRequest,
) -> MypyError:
    ignore_without_code_error: MypyError = request.param
    return ignore_without_code_error


@pytest.fixture(
    name="unused_ignore_error",
    scope="class",
    params=(
        MypyError(
            "",
            1,
            0,
            'Unused "type: ignore" comment',
            "unused-ignore",
        ),
        MypyError(
            "",
            1,
            0,
            'Unused "type: ignore[override]" comment',
            "unused-ignore",
        ),
    ),
)
def fixture_unused_ignore_error(request: pytest.FixtureRequest) -> MypyError:
    unused_ignore_error: MypyError = request.param
    return unused_ignore_error


@pytest.fixture(name="errors", scope="class")
def fixture_errors(
    errors_to_add: list[MypyError],
    ignore_without_code_error: MypyError,
    unused_ignore_error: MypyError,
) -> list[MypyError]:
    return [*errors_to_add, ignore_without_code_error, unused_ignore_error]
