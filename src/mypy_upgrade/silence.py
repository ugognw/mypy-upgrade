"""This module defines the `silence_errors` function."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import io
import itertools
import logging
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

logger = logging.getLogger(__name__)

TRY_SHOW_ABSOLUTE_PATH = (
    "Unable to find file {filename}. This may be due to running "
    "mypy in a different directory than mypy-upgrade. Please try "
    "running mypy with the --show-absolute-path flag set."
)

VERBOSITY_SUGGESTION = (
    "Run mypy-upgrade in verbose mode (option -v) to get a "
    "full print out of affected type checking errors."
)

NOT_SILENCED_WARNING = (
    "Line continuation characters and multiline (f-strings) are "
    "common culprits. Possible resolutions include: 1) "
    "formatting the affected code with a PEP 8-compliant "
    "formatter (e.g., black), 2) refactoring the affected code "
    "to avoid line continutation characters or multiline "
    "f-strings, and 3) resolving the errors."
)


class MypyUpgradeResult(NamedTuple):
    """Results from running `mypy-upgrade`

    Attributes:
        silenced: a tuple of `MypyError` instances, each of which
            representing an error that was silenced
        non_silenced: a tuple of `MypyError` instances, each of which
            representing an error that was not silenced
    """

    silenced: tuple[MypyError, ...]
    not_silenced: tuple[MypyError, ...]


def _extract_error_details(
    *,
    errors: Iterable[MypyError],
) -> tuple[list[str], list[str], list[str]]:
    """Get error codes to add/remove and descriptions to add."""
    codes_to_add: list[str] = []
    descriptions_to_add: list[str] = []
    codes_to_remove: list[str] = []
    for error in errors:
        codes_in_message = string_to_error_codes(string=error.message) or (
            "*",
        )
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
    *,
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
    to_add, descriptions, to_remove = _extract_error_details(errors=errors)
    pruned_comment = remove_unused_type_ignore_comments(
        comment=comment, codes_to_remove=to_remove
    )
    formatted_comment = format_type_ignore_comment(comment=pruned_comment)
    suppression_comment = add_type_ignore_comment(
        comment=formatted_comment,
        error_codes=to_add,
    )
    if fix_me:
        suppression_comment += f" # {fix_me}"

    if description_style == "full" and descriptions:
        suppression_comment += f" # {', '.join(descriptions)}"

    return suppression_comment


def _writelines(*, file: TextIO, lines: Iterable[CommentSplitLine]) -> int:
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


def _log_silencing_results(
    *, errors: Iterable[MypyError], safe_to_silence: Iterable[MypyError]
) -> None:
    """Logs the results of a call to `silence_errors_in_file`"""
    warned = False
    for error in errors:
        line_no = "" if not error.line_no else f":{error.line_no}"
        if error in safe_to_silence:
            logger.info(
                "Successfully silenced error: "
                f"{error.filename}{line_no}:{error.error_code}"
            )
        else:
            if warned:
                suffix = ""
            else:
                suffix = (
                    f"{NOT_SILENCED_WARNING} {VERBOSITY_SUGGESTION}"
                    if logger.level < logging.WARNING
                    else NOT_SILENCED_WARNING
                )
                warned = True
            logger.info(
                "Unable to silence error: "
                f"{error.filename}{line_no}:{error.error_code}"
                f" {suffix}".strip()
            )


def silence_errors_in_file(
    *,
    file: TextIO,
    errors: Iterable[MypyError],
    description_style: Literal["full", "none"],
    fix_me: str,
    dry_run: bool,
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
        dry_run: don't actually silence anything, just print what would be.

    Returns:
        A list of `MypyError`s which were silenced in the given file.
    """
    logger.debug(f"Silencing mypy errors: {errors}")
    errors = list(errors)
    start = file.tell()
    raw_code = file.read()
    tokens = list(tokenize.generate_tokens(io.StringIO(raw_code).readline))
    lines = split_into_code_and_comment(source=raw_code, tokens=tokens)
    safe_to_silence = filter_by_silenceability(
        errors=errors, comments=[line.comment for line in lines], tokens=tokens
    )

    for line_number, line_grouped_errors in itertools.groupby(
        safe_to_silence, key=attrgetter("line_no")
    ):
        i = line_number - 1
        new_comment = create_suppression_comment(
            comment=lines[i].comment,
            errors=line_grouped_errors,
            description_style=description_style,
            fix_me=fix_me,
        )
        lines[i] = CommentSplitLine(lines[i].code, new_comment)

    file.seek(start)

    if not dry_run:
        _ = _writelines(file=file, lines=lines)
        _ = file.truncate()
    _log_silencing_results(errors=errors, safe_to_silence=safe_to_silence)
    return safe_to_silence


def silence_errors_in_report(
    *,
    report: TextIO,
    packages: list[str],
    modules: list[str],
    files: list[str],
    description_style: Literal["full", "none"],
    fix_me: str,
    dry_run: bool,
    only_codes_to_silence: tuple[str, ...],
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
        dry_run: don't actually silence anything, just print what would be.
        only_codes_to_silence: a list of strings indicating the only mypy
            error codes to silence.

    Returns:
        A `MypyUpgradeResult` object. The errors that are silenced via type
        checking suppression comments are stored in the `silenced` attribute.
        Those that are unable to be silenced are stored in the `not_silenced`
        attribute.
    """
    errors = parse_mypy_report(report=report)
    source_filtered_errors = filter_by_source(
        errors=errors, packages=packages, modules=modules, files=files
    )
    if only_codes_to_silence:
        source_filtered_errors = [
            error
            for error in source_filtered_errors
            if error.error_code in only_codes_to_silence
        ]
    silenced: list[MypyError] = []
    for filename, filename_grouped_errors in itertools.groupby(
        errors, key=attrgetter("filename")
    ):
        try:
            with pathlib.Path(filename).open(
                mode="r+", encoding="utf-8"
            ) as file:
                safely_silenced = silence_errors_in_file(
                    file=file,
                    errors=filename_grouped_errors,
                    description_style=description_style,
                    fix_me=fix_me,
                    dry_run=dry_run,
                )
            silenced.extend(safely_silenced)
        except FileNotFoundError:
            msg = TRY_SHOW_ABSOLUTE_PATH.replace("{filename}", filename)
            logger.warning(msg)
        except tokenize.TokenError:
            msg = f"Unable to tokenize file: {filename}"
            logger.warning(msg)

    not_silenced = [e for e in source_filtered_errors if e not in silenced]
    return MypyUpgradeResult(silenced=silenced, not_silenced=not_silenced)
