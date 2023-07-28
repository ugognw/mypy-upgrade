import pathlib
import re

from mypy_upgrade.__main__ import files_to_modules


class TestFilesToModules:
    @staticmethod
    def test_should_preserve_length(shared_datadir: pathlib.Path):
        files = []
        with open(shared_datadir / "module_files.txt") as file:
            for line in file:
                files.append(line.removesuffix("\n"))

        modules = files_to_modules(files)
        assert len(modules) == len(files)

    @staticmethod
    def test_should_format_modules(shared_datadir: pathlib.Path):
        files = []
        with open(shared_datadir / "module_files.txt") as file:
            for line in file:
                files.append(line.removesuffix("\n"))

        modules = files_to_modules(files)
        fmt = re.compile(r"[^\.](\.[^\.])*")
        check = []
        for module in modules:
            check.append(fmt.match(module) is not None)

        assert False not in check
