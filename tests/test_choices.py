import argparse
from enum import Enum

import pytest
from typed_argparse import Choices


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
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])


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
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])


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
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])


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
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])


# Enums


class MyEnumPlain(Enum):
    a = "a"
    b = "b"
    c = "c"


class MyEnumStr(str, Enum):
    a = "a"
    b = "b"
    c = "c"


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_choices__empty_default__enum(
    parser: argparse.ArgumentParser, use_literal_enum: bool
) -> None:
    if use_literal_enum:
        MyEnum = MyEnumStr
    else:
        MyEnum = MyEnumPlain  # type: ignore
    parser.add_argument(
        "choices",
        nargs="*",
        type=MyEnum,
        choices=Choices(MyEnum.a, MyEnum.b, MyEnum.c),
        default=[],
    )
    assert parser.parse_args([]).choices == []
    assert parser.parse_args(["a"]).choices == [MyEnum.a]
    assert parser.parse_args(["a", "b"]).choices == [MyEnum.a, MyEnum.b]
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_choices__single_default__enum(
    parser: argparse.ArgumentParser, use_literal_enum: bool
) -> None:
    if use_literal_enum:
        MyEnum = MyEnumStr
    else:
        MyEnum = MyEnumPlain  # type: ignore
    parser.add_argument(
        "choices",
        nargs="*",
        type=MyEnum,
        choices=Choices(MyEnum.a, MyEnum.b, MyEnum.c),
        default=[MyEnum.a],
    )
    assert parser.parse_args([]).choices == [MyEnum.a]
    assert parser.parse_args(["a"]).choices == [MyEnum.a]
    assert parser.parse_args(["a", "b"]).choices == [MyEnum.a, MyEnum.b]
    with pytest.raises(SystemExit):
        parser.parse_args(["d"])
