import io
import sys
from itertools import permutations
from typing import TextIO

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import pytest

from mypy_upgrade.parsing import MypyError
from mypy_upgrade.silence import silence_errors_in_file

SAMPLE_CODE = [
    "x = 5",  # line without error
    "print(y)",  # line with error
    "x = float(z)",  # line with multiple errors
    "x = i\\\n+1",  # line with error on explicitly continued line
    "x = 1\\\n+i",  # line with error after explicitly continued line
    "x = print(f'''\n{x}\n''')",  # line with error in multiline comment
]

CODE_SUFFIXES = [
    "",
    "# noqa",
]

EXPECTED_OUTPUT_CODE = [
    "x = 5",
    "print(y)  # type: ignore[name-defined]",
    "x = float(z)  # type: ignore[assignment, used-before-def]",
    "x = i\\\n+1",
    "x = 1\\\n+i",
    "x = print(f'''\n{x}\n''')",
]

ERRORS: list[list[MypyError]] = [
    [],
    [MypyError("", 1, 7, 'Name "y" is not defined', "name-defined")],
    [
        MypyError(
            "",
            1,
            5,
            'Incompatible types in assignment (expression has type "float", '
            'variable has type "int")',
            "assignment",
        ),
        MypyError(
            "", 1, 11, 'Name "z" is used before definition', "used-before-def"
        ),
    ],
    [MypyError("", 1, 5, 'Name "i" is not defined', "name-defined")],
    [MypyError("", 1, 2, 'Name "i" is not defined', "name-defined")],
    [MypyError("", 1, 1, 'Name "i" is not defined', "name-defined")],
]

EXPECTED_SILENCED_ERRORS: list[list[MypyError]] = [
    [],
    [MypyError("", 1, 7, 'Name "y" is not defined', "name-defined")],
    [
        MypyError(
            "",
            1,
            5,
            'Incompatible types in assignment (expression has type "float", '
            'variable has type "int")',
            "assignment",
        ),
        MypyError(
            "", 1, 11, 'Name "z" is used before definition', "used-before-def"
        ),
    ],
    [],
    [],
    [],
]


@pytest.fixture(name="suffix", params=CODE_SUFFIXES)
def fixture_suffix(request: pytest.FixtureRequest) -> str:
    suffix: str = request.param
    return suffix


class TestAddErrorCodes:
    @staticmethod
    @pytest.fixture(name="index", params=range(len(SAMPLE_CODE)))
    def fixture_index(request: pytest.FixtureRequest) -> int:
        index: int = request.param
        return index

    @staticmethod
    @pytest.fixture(name="code")
    def fixture_code(index: int) -> str:
        return SAMPLE_CODE[index]

    @staticmethod
    @pytest.fixture(name="errors")
    def fixture_errors(index: int) -> list[MypyError]:
        return ERRORS[index]

    @staticmethod
    @pytest.fixture(name="expected_silenced_errors")
    def fixture_expected_silenced_errors(index: int) -> list[MypyError]:
        return EXPECTED_SILENCED_ERRORS[index]

    @staticmethod
    @pytest.fixture(name="expected_output")
    def fixture_expected_output(
        index: int,
        suffix: str,
        fix_me: str,
        description_style: str,
        expected_silenced_errors: list[MypyError],
    ) -> str:
        spacer = " " if "#" in EXPECTED_OUTPUT_CODE[index] else "  "
        expected_output = (
            f"{EXPECTED_OUTPUT_CODE[index]}{spacer}{suffix}".rstrip()
        )

        if expected_silenced_errors:
            if fix_me:
                expected_output += f" # {fix_me}"

            descriptions = [e.message for e in expected_silenced_errors]
            if description_style == "full" and descriptions:
                expected_output += f" # {', '.join(descriptions)}"
        return f"{expected_output}\n"

    @staticmethod
    @pytest.fixture(name="file")
    def fixture_file(code: str, suffix: str) -> TextIO:
        return io.StringIO(f"{code} {suffix}\n".rstrip())

    @staticmethod
    @pytest.fixture(name="silenced_errors")
    def fixture_silenced_errors(
        file: TextIO,
        errors: list[MypyError],
        description_style: Literal["full", "none"],
        fix_me: str,
    ) -> list[MypyError]:
        return silence_errors_in_file(
            file=file,
            errors=iter(errors),
            description_style=description_style,
            fix_me=fix_me,
        )

    @staticmethod
    def test_should_silence_file_appropriately(
        silenced_errors: list[MypyError],  # noqa: ARG004
        file: TextIO,
        expected_output: str,
    ) -> None:
        start = file.tell()
        file.seek(0)
        contents = file.read()
        file.seek(start)
        assert contents == expected_output

    @staticmethod
    def test_should_return_silenced_errors(
        silenced_errors: list[MypyError],
        expected_silenced_errors: list[MypyError],
    ) -> None:
        assert all(
            error in silenced_errors for error in expected_silenced_errors
        )


ERROR_CODES = ["assignment", "arg-type", "used-before-def"]
CODE_COMBINATIONS = [*permutations(ERROR_CODES, r=2), ERROR_CODES]


class TestRemoveErrorCodes:
    @staticmethod
    @pytest.fixture(name="error_codes", params=CODE_COMBINATIONS)
    def fixture_error_codes(request: pytest.FixtureRequest) -> list[str]:
        error_codes: list[str] = request.param
        return error_codes

    @staticmethod
    @pytest.fixture(name="codes_to_remove", params=CODE_COMBINATIONS)
    def fixture_codes_to_remove(error_codes: list[str]) -> list[str]:
        codes_to_remove: list[str] = error_codes[:-1]
        return codes_to_remove

    @staticmethod
    @pytest.fixture(name="unused_ignore")
    def fixture_unused_ignore_ignore(codes_to_remove: list[str]) -> MypyError:
        return MypyError(
            "",
            1,
            0,
            f'Unused "type: ignore[{", ".join(codes_to_remove)}]" comment',
            "unused-ignore",
        )

    @staticmethod
    @pytest.fixture(name="type_ignore")
    def fixture_type_ignore(error_codes: list[str]) -> str:
        return f"type: ignore[{', '.join(error_codes)}]"

    @staticmethod
    @pytest.fixture(name="suffix", params=CODE_SUFFIXES)
    def fixture_suffix(request: pytest.FixtureRequest) -> str:
        suffix: str = request.param
        return suffix

    @staticmethod
    @pytest.fixture(name="comment")
    def fixture_comment(type_ignore: str, suffix: str) -> str:
        return f"# {type_ignore} {suffix}".rstrip()

    @staticmethod
    @pytest.fixture(name="file")
    def fixture_file(comment: str) -> TextIO:
        return io.StringIO(f"x = 5  {comment}")

    @staticmethod
    @pytest.fixture(name="silenced_errors")
    def fixture_silenced_errors(
        file: TextIO,
        unused_ignore: MypyError,
        description_style: Literal["full", "none"],
        fix_me: str,
    ) -> list[MypyError]:
        return silence_errors_in_file(
            file=file,
            errors=iter([unused_ignore]),
            description_style=description_style,
            fix_me=fix_me,
        )

    @staticmethod
    def test_should_remove_error_codes_if_codes_to_remove_not_superset_of_existing_codes(  # noqa: E501
        file: TextIO,
        codes_to_remove: list[str],
        silenced_errors: list[MypyError],  # noqa: ARG004
    ) -> None:
        start = file.tell()
        output = file.read()
        file.seek(start)
        assert not any(code in output for code in codes_to_remove)


# line with no error
# line with error
# line with multiple errors

# line with error (code to add, code to remove)
# line with no error (code[s] to remove)
# line with error in multiline comment (inside and end)
# line with error in explicitly continued line
# line with comment


# Silence multiple errors in file
# Silence multiple errors on line
# Silence errors with existing comments
# Silence errors with existing "type: ignore" comments
# Remove existing "type: ignore" comments
