"""This module defines the `silence_errors` function."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import itertools
import pathlib
import sys
import tokenize
from collections.abc import Iterable, Iterator
from typing import NamedTuple

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.editing import (
    add_type_ignore_comment,
    format_type_ignore_comment,
    remove_unused_type_ignore_comment,
)
from mypy_upgrade.filter import filter_mypy_errors
from mypy_upgrade.parsing import (
    MypyError,
    parse_mypy_report,
    string_to_error_codes,
)
from mypy_upgrade.utils import (
    get_lines_and_tokens,
    get_safe_to_silence_errors,
    split_into_code_and_comment,
)
from mypy_upgrade.warnings import MISSING_ERROR_CODES, TRY_SHOW_ABSOLUTE_PATH


class MypyUpgradeResult(NamedTuple):
    """Results from running `mypy-upgrade`

    Attributes:
        silenced: a tuple of `MypyError` instances, each of which
            representing an error that was silenced
        non_silenced: a tuple of `MypyError` instances, each of which
            representing an error that was not silenced
        messages: a tuple of strings representing messages produced during
            execution of `mypy-upgrade`
    """

    silenced: tuple[MypyError, ...]
    not_silenced: tuple[MypyError, ...]
    messages: tuple[str, ...]


def _collect_errors(report: pathlib.Path | None) -> list[MypyError]:
    """Parse errors from provided file or standard input."""
    if report is not None:
        with pathlib.Path(report).open(encoding="utf-8") as file:
            return parse_mypy_report(file)
    return parse_mypy_report(sys.stdin)


def _extract_error_details(
    errors: Iterable[MypyError],
) -> tuple[list[str], list[str], str | None]:
    """Get error codes/descriptions to add and message from error to remove."""
    error_codes = []
    descriptions = []
    to_remove_message: str | None = None
    for error in errors:
        if error.error_code == "unused-ignore":
            to_remove_message = error.message
        elif error.error_code == "ignore-without-code":
            suggested_error_codes = string_to_error_codes(error.message)
            # any error codes in error.message will be used to silence errors
            if suggested_error_codes:
                for error_code in suggested_error_codes:
                    if error_code not in error_codes:
                        error_codes.append(error_code)
                        descriptions.append("")
            # 0 error codes in error.message = unused `type: ignore`
            else:
                to_remove_message = to_remove_message or ""
        elif error.error_code not in error_codes:
            error_codes.append(error.error_code)
            descriptions.append(error.message)

    return error_codes, descriptions, to_remove_message


def _generate_suppression_comment(
    comment: str,
    codes_to_add: list[str],
    error_message: str,
) -> str:
    """Generates comment for error suppression."""
    if error_message is None:
        cleaned_comment = comment
    else:
        codes_to_remove = string_to_error_codes(error_message)
        pruned_comment = remove_unused_type_ignore_comment(
            comment, codes_to_remove
        )
        cleaned_comment = format_type_ignore_comment(pruned_comment)

    if codes_to_add:
        return add_type_ignore_comment(
            cleaned_comment,
            codes_to_add,
        )
    return cleaned_comment


def silence_errors_on_line(
    python_code: str,
    comment: str,
    errors: Iterable[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> str:
    """Silences the given error on a line with an error code-specific comment.

    Args:
        python_code: a string representing the executable Python code on a
            physical line.
        comment: a string representing the comment on a physical line of
            Python code.
        error: an `Iterable` in which each entry is a `MypyError` to be
            silenced.
        description_style: a string specifying the style of the description of
            errors.
        fix_me: a string specifying a "fix me" message to be appended after the
            silencing comment.
    Returns:
        The line with a type error suppression comment.
    """
    codes_to_add, descriptions, message = _extract_error_details(errors)

    comment_with_suppression = _generate_suppression_comment(
        comment, codes_to_add, message
    )

    updated_line = f"{python_code}  {comment_with_suppression}".rstrip()

    if fix_me:
        updated_line += f" # {fix_me}"

    if description_style == "full" and descriptions:
        updated_line += f" # {', '.join(descriptions)}"

    return updated_line + "\n"


def silence_errors_in_file(
    filename: str,
    errors: Iterator[MypyError],
    description_style: str,
    fix_me: str,
) -> list[MypyError]:
    with pathlib.Path(filename).open(encoding="utf-8") as f:
        lines, tokens = get_lines_and_tokens(f)

    comments = [t for t in tokens if t.exact_type == tokenize.COMMENT]
    safe_to_silence = get_safe_to_silence_errors(tokens, comments, errors)

    for line_number, line_grouped_errors in itertools.groupby(
        safe_to_silence, key=lambda error: error.line_no
    ):
        python_code, comment = split_into_code_and_comment(
            lines[line_number - 1], comments
        )

        lines[line_number - 1] = silence_errors_on_line(
            python_code,
            comment,
            line_grouped_errors,
            description_style,
            fix_me,
        )

    with pathlib.Path(filename).open(mode="w", encoding="utf-8") as f:
        _ = f.write("".join(lines))

    return safe_to_silence


def silence_errors_in_report(
    report: pathlib.Path | None,
    packages: list[str],
    modules: list[str],
    files: list[str],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> MypyUpgradeResult:
    """Silence errors listed in a given mypy error report.

    If `packages`, `modules`, and `files` are all empty, all errors listed in
    the report will be silenced.

    Args:
        report: an optional `pathlib.Path` pointing to the the mypy error
            report. If `None`, the report is read from the standard input.
        packages: a list of strings representing the packages in which to
            silence errors.
        modules: a list of strings representing the modules in which to
            silence errors.
        files: a list of strings representing the files in which to
            silence errors.
        description_style: a string specifying the style of error descriptions
            appended to the end of error suppression comments. A value of
            "full" appends the complete error message. A value of "none"
            does not append anything.
        fix_me: a string specifying the 'Fix Me' message in type error
            suppresion comments. Pass "" to omit a 'Fix Me' message
            altogether. All trailing whitespace will be trimmed.

    Returns:
        A `MypyUpgradeResult` object. The errors that are silenced via type
        checking suppression comments are stored in the `silenced` attribute.
        Those that are unable to be silenced are stored in the `not_silenced`
        attribute. If a `FileNotFoundError` is raised while reading a file in
        which an error is to be silenced or `mypy-upgrade`-related warnings
        are raised during execution are stored in the `messages` attribute.
    """
    errors = _collect_errors(report)
    filtered_errors = filter_mypy_errors(errors, packages, modules, files)
    messages = []
    silenced: list[MypyError] = []
    for filename, filename_grouped_errors in itertools.groupby(
        errors, key=lambda error: error.filename
    ):
        try:
            silenced = silence_errors_in_file(
                filename, filename_grouped_errors, description_style, fix_me
            )
        except FileNotFoundError:
            messages += TRY_SHOW_ABSOLUTE_PATH.replace("{filename}", filename)
        except tokenize.TokenError:
            messages += f"Unable to tokenize file: {filename}"

    if any(error.error_code is None for error in filtered_errors):
        messages += MISSING_ERROR_CODES

    not_silenced = [e for e in filtered_errors if e not in silenced]
    return MypyUpgradeResult((*silenced,), (*not_silenced,), (*messages,))
