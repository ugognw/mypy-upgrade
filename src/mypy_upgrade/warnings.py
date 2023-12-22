"""This module defines warnings strings and functions to create them."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_upgrade.parsing import MypyError


def create_not_silenced_errors_warning(
    *, not_silenced: tuple[MypyError, ...], verbosity: int = 0
) -> str:
    """Create a warning for the user about errors that were not silenced.

    Args:
        not_silenced: a list of MypyErrors that were not silenced.
        verbosity: an integer indicating the verbosity level for printing

    Returns:
        A string containing the warning.
    """
    num_not_silenced = len(not_silenced)
    verb = "error was not" if num_not_silenced == 1 else "errors were not"

    warning_stem = (
        f"{num_not_silenced} {verb} not silenced due to syntax "
        "limitations.\n\n"
    )
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
