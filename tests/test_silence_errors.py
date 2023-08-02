import os
import pathlib
import sys

import pytest

from mypy_upgrade.cli import main


@pytest.mark.skip(reason="need to refactor functional test")
def test(shared_datadir: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = str(shared_datadir / "mypy_fix-1267.txt")

    with monkeypatch.context() as mp:
        os.chdir("/Users/ugo/Projects/nwt/ase")
        mp.syspath_prepend("/Users/ugo/Projects/nwt/ase")
        mp.setattr(
            sys, "argv", [sys.argv[0], "--package", "ase", "--report", report]
        )
        main()


def test_should_add_comment_to_bare_line() -> None:
    pass


def test_should_combine_comments1() -> None:
    pass


def test_should_combine_comments2() -> None:
    pass
