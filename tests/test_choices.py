import argparse
from enum import Enum
from typing import List

import pytest
from typing_extensions import Literal

from typed_argparse import Choices, TypedArgs, get_choices_from


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


# get_choices_from


def test_get_choices_from() -> None:
    class EnumInt(Enum):
        a = 1
        b = 2
        c = 3

    assert get_choices_from(Literal[1, 2, 3]) == [1, 2, 3]
    assert get_choices_from(EnumInt) == [EnumInt.a, EnumInt.b, EnumInt.c]

    # Support list wrapping
    assert get_choices_from(List[Literal[1, 2, 3]]) == [1, 2, 3]
    assert get_choices_from(List[EnumInt]) == [EnumInt.a, EnumInt.b, EnumInt.c]


def test_get_choices_from_class() -> None:
    class EnumInt(Enum):
        a = 1
        b = 2
        c = 3

    class EnumStr(Enum):
        a = "a"
        b = "b"
        c = "c"

    class MyClass(TypedArgs):
        lit_int: Literal[1, 2, 3]
        lit_str: Literal["a", "b", "c"]
        enum_int: EnumInt
        enum_str: EnumStr
        not_a_lit: int

    assert MyClass.get_choices_from("lit_int") == [1, 2, 3]
    assert MyClass.get_choices_from("lit_str") == ["a", "b", "c"]

    assert MyClass.get_choices_from("enum_int") == [EnumInt.a, EnumInt.b, EnumInt.c]
    assert MyClass.get_choices_from("enum_str") == [EnumStr.a, EnumStr.b, EnumStr.c]

    with pytest.raises(
        TypeError,
        match="Could not infer literal values of field 'not_a_lit' of type 'int'",
    ):
        MyClass.get_choices_from("not_a_lit")

    with pytest.raises(
        TypeError,
        match="Class MyClass doesn't have a type annotation for field 'non_existing'",
    ):
        MyClass.get_choices_from("non_existing")
