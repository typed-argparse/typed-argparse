import argparse
from typed_argparse import Choices

import pytest


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()


def test_choices__empty_default(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "choices",
        nargs="*",
        choices=Choices("a", "b", "c"),
        default=[],
    )
    assert parser.parse_args([]).choices == []
    assert parser.parse_args(["a"]).choices == ["a"]
    assert parser.parse_args(["a", "b"]).choices == ["a", "b"]
    assert parser.parse_args(["a", "b", "c"]).choices == ["a", "b", "c"]


def test_choices__single_default(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "choices",
        nargs="*",
        choices=Choices("a", "b", "c"),
        default=["a"],
    )
    assert parser.parse_args([]).choices == ["a"]
    assert parser.parse_args(["a"]).choices == ["a"]
    assert parser.parse_args(["a", "b"]).choices == ["a", "b"]
    assert parser.parse_args(["a", "b", "c"]).choices == ["a", "b", "c"]


def test_choices__full_default(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "choices",
        nargs="*",
        choices=Choices("a", "b", "c"),
        default=["a", "b", "c"],
    )
    assert parser.parse_args([]).choices == ["a", "b", "c"]
    assert parser.parse_args(["a"]).choices == ["a"]
    assert parser.parse_args(["a", "b"]).choices == ["a", "b"]
    assert parser.parse_args(["a", "b", "c"]).choices == ["a", "b", "c"]


def test_choices__full_default_from_choices(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "choices",
        nargs="*",
        choices=Choices("a", "b", "c"),
        default=Choices("a", "b", "c"),
    )
    assert parser.parse_args([]).choices == ["a", "b", "c"]
    assert parser.parse_args(["a"]).choices == ["a"]
    assert parser.parse_args(["a", "b"]).choices == ["a", "b"]
    assert parser.parse_args(["a", "b", "c"]).choices == ["a", "b", "c"]
