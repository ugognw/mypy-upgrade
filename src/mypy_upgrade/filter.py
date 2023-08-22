"""This module defines functions for filtering mypy type checking errors."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import importlib.abc
import pathlib
import tokenize
from collections.abc import Iterable, Sequence
from importlib import util
from typing import NamedTuple

from mypy_upgrade.parsing import MypyError


def _get_module_paths(modules: list[str]) -> list[pathlib.Path | None]:
    """Determine file system paths of given modules/packages.

    Args:
        modules: a list of strings representing (importable) modules.

    Returns:
        A list (of the same length as the input list) of pathlib.Path objects
        corresponding to the given modules. If a path is not found for a
        module, the corresponding entry in the output is ``None``.

    Raises:
        NotImplementedError: Uncountered an unsupported module type.
    """
    paths: list[pathlib.Path | None] = []
    for module in modules:
        spec = util.find_spec(module)
        if spec is None:
            paths.append(None)
        else:
            loader = spec.loader
            if isinstance(loader, importlib.abc.ExecutionLoader):
                module_path = pathlib.Path(loader.get_filename(module))
                if loader.is_package(module):
                    module_path = module_path.parent
            elif spec.origin == "frozen":
                module_path = pathlib.Path(spec.loader_state.filename)
            else:
                msg = "Uncountered an unsupported module type."
                raise NotImplementedError(msg)
            paths.append(module_path)

    return paths


def filter_by_source(
    *,
    errors: list[MypyError],
    packages: list[str],
    modules: list[str],
    files: list[str],
) -> list[MypyError]:
    """Filter `MypyError`s by source (e.g., packages, modules, files).

    Args:
        errors: a list of `MypyError`s.
        packages: a list of strings specifying packages to be included.
        modules: a list of strings specifying modules to be included.
        files: a list of strings specifying files to be included.

    Returns:
        A list of `MypyError`s including only those in either ``packages``,
        ``modules``, or ``files``.
    """
    if len(packages + modules + files) == 0:
        return errors

    package_paths = [p for p in _get_module_paths(packages) if p is not None]
    module_paths = [m for m in _get_module_paths(modules) if m is not None]
    file_paths = [pathlib.Path(f).resolve() for f in files]
    paths = package_paths + module_paths + file_paths
    selected = []
    for error in errors:
        module_path = pathlib.Path(error.filename).resolve()
        # ! Use Path.is_relative_to when dropping Python 3.7-3.8 support
        should_include = any(
            path in module_path.parents or path == module_path
            for path in paths
        )

        if should_include:
            selected.append(error)

    return selected


class UnsilenceableRegion(NamedTuple):
    """A region within a source code that cannot be silenced by an inline
    comment.

    Attributes:
        start: an integer representing the start line of the unsilenceable
            region (1-indexed).
        end: an integer representing the end line of the unsilenceable
            region (1-indexed).

        When start = end, it is interpreted that the Unsilenceable
        region is an explicitly continued line.
    """

    start: int
    end: int


def _find_unsilenceable_regions(
    *,
    tokens: Iterable[tokenize.TokenInfo],
    comments: Sequence[str],
) -> list[UnsilenceableRegion]:
    """Find the regions encapsulated by line continuation characters or
    by multiline strings.

    Args:
        tokens: an iterable containing `TokenInfo` objects.
        comments: a sequence of strings representing code comments-one for
            each line in the source from which `tokens` is generated.

    Returns:
        A list of `UnsilenceableRegion` objects.

        Multiline strings are represented by `UnsilenceableRegion` objects
        whose first entries in their `start` and `end` attributes differ.
        Explicitly continued lines are represented by `UnsilenceableRegion`
        objects whose first entries in their `start` and `end` attributes are
        the same.
    """
    unsilenceable_regions: set[UnsilenceableRegion] = set()
    for token in tokens:
        if (
            token.start[0] != token.end[0]
            and token.exact_type == tokenize.STRING
        ):
            region = UnsilenceableRegion(token.start[0], token.end[0])
            unsilenceable_regions.add(region)
        elif (
            token.line.rstrip("\r\n").endswith("\\")
            and not comments[token.end[0] - 1]
        ):
            region = UnsilenceableRegion(token.end[0], token.end[0])
            unsilenceable_regions.add(region)

    return list(unsilenceable_regions)


def _is_safe_to_silence(
    *, error: MypyError, unsilenceable_regions: Iterable[UnsilenceableRegion]
) -> bool:
    """Determine if the error is safe to silence

    Args:
        error: a `MypyError` for which a type error suppression comment is to
            placed.
        unsilenceable_regions: an iterable of `UnsilenceableRegion`s.

    Returns:
        `False` if the error is in an `UnsilenceableRegion` or its error code
        is "syntax"; `True` otherwise.
    """
    if error.error_code == "syntax":
        return False

    for region in unsilenceable_regions:
        # Error within an UnsilenceableRegion (but not last line of multiline
        # string)
        if region.start <= error.line_no <= region.end and not (
            error.line_no == region.end and region.start != region.end
        ):
            return False

    return True


def filter_by_silenceability(
    *,
    errors: Iterable[MypyError],
    comments: Sequence[str],
    tokens: Iterable[tokenize.TokenInfo],
) -> list[MypyError]:
    """Filter `MypyError`s by those which are safe to silence.

    Args:
        errors: the errors whose line numbers are to be corrected.
        comments: a container of strings representing code comments.
        tokens: an iterable containing `TokenInfo` objects.

    Returns:
        A list in which each entry is a `MypyError` from `errors` that can be
        silenced with a type suppression comment.
    """
    unsilenceable_regions = _find_unsilenceable_regions(
        tokens=tokens, comments=comments
    )
    safe_to_silence = []
    for error in errors:
        if _is_safe_to_silence(
            error=error, unsilenceable_regions=unsilenceable_regions
        ):
            safe_to_silence.append(error)

    return safe_to_silence
