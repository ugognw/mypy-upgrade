from __future__ import annotations

from mypy_upgrade.parsing import MypyError

MISSING_ERROR_CODES = (
    "Not all errors in the mypy type checking report have error "
    "codes. As a result, mypy-upgrade can only suppress these errors "
    "with non-code-specific # type: ignore comments (which will still "
    "raise errors when running mypy with --strict enabled). If you "
    "would like mypy-upgrade to silence errors with code-specific "
    "comments, please run mypy with --show-error-codes enabled. "
    "If you would like to suppress this warning, use the "
    "--allow-no-error-codes flag for mypy-upgrade."
)

TRY_SHOW_ABSOLUTE_PATH = (
    "Unable to find file {filename}. This may be due to running"
    "mypy in a different directory than mypy-upgrade. Please try "
    "running mypy with the --show-absolute-path flag set."
)


def create_not_silenced_errors_warning(
    not_silenced: list[MypyError], verbosity: int = 0
) -> str:
    """Create a warning for the user about errors that were not silenced.

    Args:
        not_silenced: a list of MypyErrors that were not silenced.
        verbosity: an integer indicating the verbosity level for printing

    Returns:
        A string containing the warning.
    """
    if len(not_silenced) == 0:
        with_column_numbers = False
    else:
        with_column_numbers = all(
            err.col_offset is not None for err in not_silenced
        )

    num_not_silenced = len(not_silenced)
    verb = "error was not" if num_not_silenced == 1 else "errors were not"

    warning_stem = (
        f"{num_not_silenced} {verb} not silenced due to syntax "
        "limitations.\n\n"
    )
    if not with_column_numbers:
        warning_suffix = (
            "Consider using the --show-column-numbers flag when "
            "generating the mypy type checking report."
        )
    else:
        if verbosity < 1:
            verbose_suggestion = (
                "\n\nRun mypy-upgrade in verbose mode (option -v) to get a "
                "full print out of affected type checking errors."
            )
        else:
            verbose_suggestion = ""

        warning_suffix = (
            "Line continuation characters and multiline (f-strings) are "
            "common culprits. Possible resolutions include: 1) "
            "formatting the affected code with a PEP 8-compliant "
            "formatter (e.g., black), 2) refactoring the affected code "
            "to avoid line continutation characters or multiline "
            "f-strings, and 3) resolving the errors."
            f"{verbose_suggestion}"
        )

    return warning_stem + warning_suffix
