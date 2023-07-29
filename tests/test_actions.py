import argparse
import pathlib
import sys

import pytest

from mypy_upgrade.__main__ import Split, StorePath


@pytest.fixture(name="name", params=["argument", "--option"])
def fixture_name(request) -> str:
    return request.param


@pytest.fixture(name="args")
def fixture_args(
    name, action, request: pytest.FixtureRequest
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(name, action=action)
    value = request.node.get_closest_marker("value").args[0]
    args = [name, value] if "--" in name else [value]
    sys.argv.extend(args)
    yield parser.parse_args(args)
    try:
        sys.argv.remove(name)
    except ValueError:
        try:
            sys.argv.remove(value)
        except ValueError:
            pass


class TestSplit:
    @staticmethod
    @pytest.fixture(name="action")
    def fixture_action() -> type:
        return Split

    @staticmethod
    @pytest.mark.value("test")
    def test_should_remove_argument_from_stdin1(name: str):
        assert name.removeprefix("--") not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value("test1,test2")
    def test_should_remove_argument_from_stdin2(name: str):
        assert name.removeprefix("--") not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value("test")
    def test_should_remove_value_from_stdin1():
        assert "test" not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value("test1,test2")
    def test_should_remove_value_from_stdin2():
        assert "test" not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value("test")
    def test_should_store_split_into_list1(
        args: argparse.Namespace, name: str
    ):
        assert vars(args)[name.removeprefix("--")] == ["test"]

    @staticmethod
    @pytest.mark.value("test1,test2")
    def test_should_store_split_into_list2(
        args: argparse.Namespace, name: str
    ):
        assert vars(args)[name.removeprefix("--")] == ["test1", "test2"]


class TestStorePath:
    @staticmethod
    @pytest.fixture(name="action")
    def fixture_action() -> type:
        return StorePath

    @staticmethod
    @pytest.mark.value(__file__)
    def test_should_remove_argument_from_stdin(name: str):
        assert name.removeprefix("--") not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value(__file__)
    def test_should_remove_value_from_stdin():
        assert __file__ not in sys.argv[1:]

    @staticmethod
    @pytest.mark.value(__file__)
    def test_should_store_path(args: argparse.Namespace, name: str):
        assert vars(args)[name.removeprefix("--")] == pathlib.Path(__file__)
