"""This module defines functions for filtering mypy type checking errors."""
# remove when dropping Python 3.7-3.9 support
from __future__ import annotations

import importlib.abc
import pathlib
from importlib import util

from mypy_upgrade.parsing import MypyError


def get_module_paths(modules: list[str]) -> list[pathlib.Path | None]:
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
            elif spec.origin == "built-in":
                pass  # ? Maybe should raise a warning
            else:
                msg = "Uncountered an unsupported module type."
                raise NotImplementedError(msg)
            paths.append(module_path)

    return paths


def filter_mypy_errors(
    errors: list[MypyError],
    packages: list[str],
    modules: list[str],
    files: list[str],
) -> list[MypyError]:
    """Select errors based on specified packages, modules, files.

    Args:
        errors: a list of MypyErrors.
        packages: a list of strings specifying packages to be included.
        modules: a list of strings specifying modules to be included.
        files: a list of strings specifying files to be included.

    Returns:
        A list of MypyErrors including only those in either ``packages``,
        ``modules``, or ``files``.
    """
    if len(packages + modules + files) == 0:
        return errors

    package_paths = [p for p in get_module_paths(packages) if p is not None]
    module_paths = [m for m in get_module_paths(modules) if m is not None]
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
