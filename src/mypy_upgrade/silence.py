"""This module defines the `silence_errors` function."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import itertools
import pathlib
import sys
import tokenize
from collections.abc import Iterable
from operator import attrgetter
from typing import NamedTuple, TextIO

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from mypy_upgrade.editing import (
    add_type_ignore_comment,
    format_type_ignore_comment,
    remove_unused_type_ignore_comments,
)
from mypy_upgrade.filter import filter_by_silenceability, filter_by_source
from mypy_upgrade.parsing import (
    MypyError,
    parse_mypy_report,
    string_to_error_codes,
)
from mypy_upgrade.utils import (
    CommentSplitLine,
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


def _extract_error_details(
    errors: Iterable[MypyError],
) -> tuple[list[str], list[str], list[str]]:
    """Get error codes to add/remove and descriptions to add."""
    codes_to_add: list[str] = []
    descriptions_to_add: list[str] = []
    codes_to_remove: list[str] = []
    for error in errors:
        codes_in_message = string_to_error_codes(error.message) or ("*",)
        if error.error_code == "unused-ignore" or (
            # 0 error codes in error.message = unused `type: ignore`
            error.error_code == "ignore-without-code"
            and "*" in codes_in_message
        ):
            codes_to_remove.extend(codes_in_message)
        elif error.error_code == "ignore-without-code":
            codes_to_add.extend(codes_in_message)
            descriptions_to_add.extend("No message" for _ in codes_in_message)
        else:
            codes_to_add.append(error.error_code)
            descriptions_to_add.append(error.message)

    return codes_to_add, descriptions_to_add, codes_to_remove


def create_suppression_comment(
    comment: str,
    errors: Iterable[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> str:
    """Produce a type error suppression comment from the given errors.

    Args:
        comment: a string representing the comment on a physical line of
            Python code.
        errors: an `Iterable` in which each entry is a `MypyError` to be
            silenced.
        description_style: a string specifying the style of the description of
            errors.
        fix_me: a string specifying a "fix me" message to be appended after the
            silencing comment.
    Returns:
        A type error suppression comment.
    """
    to_add, descriptions, to_remove = _extract_error_details(errors)
    pruned_comment = remove_unused_type_ignore_comments(comment, to_remove)
    formatted_comment = format_type_ignore_comment(pruned_comment)
    suppression_comment = add_type_ignore_comment(
        formatted_comment,
        to_add,
    )
    if fix_me:
        suppression_comment += f" # {fix_me}"

    if description_style == "full" and descriptions:
        suppression_comment += f" # {', '.join(descriptions)}"

    return suppression_comment


def _writelines(file: TextIO, lines: Iterable[CommentSplitLine]) -> int:
    """Write an iterable of `CommentSplitLine`s to a file."""
    to_write = []
    for line in lines:
        if line.code and line.comment:
            if line.code.endswith(" ") and not line.comment.startswith(
                "# type: ignore"
            ):
                to_write.append(f"{line.code}{line.comment}")
            else:
                to_write.append(f"{line.code.rstrip()}  {line.comment}")
        elif line.code:
            to_write.append(line.code)
        else:
            to_write.append(line.comment)
    return file.write("\n".join(to_write))


def silence_errors_in_file(
    file: TextIO,
    errors: Iterable[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
) -> list[MypyError]:
    """Silence errors in a given file.

    Args:
        file: A `TextIO` instance opened for both reading and writing.
        errors: an iterable of `MypyError`s.
        description_style:  a string specifying the style of error descriptions
            appended to the end of error suppression comments.

                - A value of "full" appends the complete error message.
                - A value of "none" does not append anything.

        fix_me: a string specifying the 'Fix Me' message in type error
            suppresion comments. Pass "" to omit a 'Fix Me' message
            altogether. All trailing whitespace will be trimmed.

    Returns:
        A list of `MypyError`s which were silenced in the given file.
    """
    start = file.tell()
    raw_code = file.read()
    tokens = list(tokenize.generate_tokens(io.StringIO(raw_code).readline))
    lines = split_into_code_and_comment(raw_code, tokens)
    safe_to_silence = filter_by_silenceability(
        errors=errors, comments=[line.comment for line in lines], tokens=tokens
    )

    for line_number, line_grouped_errors in itertools.groupby(
        safe_to_silence, key=attrgetter("line_no")
    ):
        i = line_number - 1
        new_comment = create_suppression_comment(
            lines[i].comment,
            line_grouped_errors,
            description_style,
            fix_me,
        )
        lines[i] = CommentSplitLine(lines[i].code, new_comment)

    file.seek(start)
    _ = _writelines(file, lines)
    _ = file.truncate()
    return safe_to_silence


def silence_errors_in_report(
    report: TextIO,
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
        report: a text I/O opened for reading which contains the `mypy`
            error report text.
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
    errors = parse_mypy_report(report)
    source_filtered_errors = filter_by_source(
        errors=errors, packages=packages, modules=modules, files=files
    )
    messages: list[str] = []
    silenced: list[MypyError] = []
    for filename, filename_grouped_errors in itertools.groupby(
        errors, key=attrgetter("filename")
    ):
        try:
            with pathlib.Path(filename).open(
                mode="r+", encoding="utf-8"
            ) as file:
                safe_to_silence = silence_errors_in_file(
                    file,
                    filename_grouped_errors,
                    description_style,
                    fix_me,
                )
            silenced.extend(safe_to_silence)
        except FileNotFoundError:
            messages += TRY_SHOW_ABSOLUTE_PATH.replace("{filename}", filename)
        except tokenize.TokenError:
            messages += f"Unable to tokenize file: {filename}"

    if any(error.error_code is None for error in source_filtered_errors):
        messages += MISSING_ERROR_CODES

    not_silenced = [e for e in source_filtered_errors if e not in silenced]
    return MypyUpgradeResult((*silenced,), (*not_silenced,), (*messages,))
