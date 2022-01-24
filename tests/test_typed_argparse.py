from typed_argparse import TypedArgs, WithUnionType, get_choices_from

import enum
import argparse
import pytest

from typing import List, Optional, Union
from typing_extensions import Literal


# -----------------------------------------------------------------------------
# Basics
# -----------------------------------------------------------------------------


def test_basic_1() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"


def test_basic_2() -> None:
    class MyArgs(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num=42)
    args = MyArgs(args_namespace)
    assert args.num == 42


def test_missing_field__single() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace()
    with pytest.raises(
        TypeError,
        match="Arguments object is missing argument 'foo'",
    ):
        MyArgs(args_namespace)


def test_missing_field__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str
        bar: str

    args_namespace = argparse.Namespace()
    with pytest.raises(
        TypeError,
        match=r"Arguments object is missing arguments \['foo', 'bar'\]",
    ):
        MyArgs(args_namespace)


def test_extra_field__single() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar")
    with pytest.raises(
        TypeError,
        match="Arguments object has an unexpected extra argument 'bar'",
    ):
        MyArgs(args_namespace, disallow_extra_args=True)


def test_extra_field__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar", baz="baz")
    with pytest.raises(
        TypeError,
        match=r"Arguments object has unexpected extra arguments \['bar', 'baz'\]",
    ):
        MyArgs(args_namespace, disallow_extra_args=True)


def test_simple_type_mismatch_1() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'foo': value is of type 'int', expected 'str'",
    ):
        MyArgs(args_namespace)


def test_simple_type_mismatch_2() -> None:
    class MyArgs(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num="foo")
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'num': value is of type 'str', expected 'int'",
    ):
        MyArgs(args_namespace)


def test_annotation_that_isnt_a_type() -> None:
    # In principle this should already be prevented by mypy itself (that's why we
    # need to type-ignore the mistake here), but let's make sure that it still
    # would produce a comprehensible runtime error.
    class MyArgs(TypedArgs):
        num: 42  # type: ignore

    args_namespace = argparse.Namespace(num=42)
    with pytest.raises(
        TypeError,
        match="Failed to validate argument 'num': "
        "Type annotation is of type 'int', expected 'type'",
    ):
        MyArgs(args_namespace)


# -----------------------------------------------------------------------------
# Lists
# -----------------------------------------------------------------------------


def test_lists_1() -> None:
    class MyArgs(TypedArgs):
        foo: List[str]

    args_namespace = argparse.Namespace(foo=["a", "b", "c"])
    args = MyArgs(args_namespace)
    assert args.foo == ["a", "b", "c"]


def test_lists_2() -> None:
    class MyArgs(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=[1, 2, 3])
    args = MyArgs(args_namespace)
    assert args.num == [1, 2, 3]


def test_lists__should_coerce_empty_lists_automatically() -> None:
    class MyArgs(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=None)
    args = MyArgs(args_namespace)
    assert args.num == []


def test_lists__should_not_coerce_empty_lists_automatically_if_optional() -> None:
    class MyArgs(TypedArgs):
        num: Optional[List[int]]

    args_namespace = argparse.Namespace(num=None)
    args = MyArgs(args_namespace)
    assert args.num is None


def test_lists__elements_type_mismatch_1() -> None:
    class MyArgs(TypedArgs):
        foo: List[str]

    args_namespace = argparse.Namespace(foo=["a", 2, "c"])
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'foo': not all elements "
        r"of the list have proper type \(value is of type 'int', expected 'str'\)",
    ):
        MyArgs(args_namespace)


def test_lists__elements_type_mismatch_2() -> None:
    class MyArgs(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=["a", 2, "c"])
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'num': not all elements "
        r"of the list have proper type \(value is of type 'str', expected 'int'\)",
    ):
        MyArgs(args_namespace)


# -----------------------------------------------------------------------------
# Optionals
# -----------------------------------------------------------------------------


def test_optional_1() -> None:
    class MyArgs(TypedArgs):
        foo: Optional[str]

    args_namespace = argparse.Namespace(foo=None)
    args = MyArgs(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"


def test_optional_2() -> None:
    class MyArgs(TypedArgs):
        num: Optional[int]

    args_namespace = argparse.Namespace(num=None)
    args = MyArgs(args_namespace)
    assert args.num is None

    args_namespace = argparse.Namespace(num=42)
    args = MyArgs(args_namespace)
    assert args.num == 42


def test_optional__type_mismatch() -> None:
    class MyArgs(TypedArgs):
        foo: Optional[str]

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError, match="Failed to validate argument 'foo': value is of type 'int', expected 'str'"
    ):
        MyArgs(args_namespace)


def test_optional_as_union_type_1() -> None:
    class MyArgs(TypedArgs):
        foo: Union[str, None]

    args_namespace = argparse.Namespace(foo=None)
    args = MyArgs(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"


def test_optional_as_union_type_2() -> None:
    class MyArgs(TypedArgs):
        foo: Union[None, str]

    args_namespace = argparse.Namespace(foo=None)
    args = MyArgs(args_namespace)
    assert args.foo is None

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"


def test_string_representation() -> None:
    class MyArgs(TypedArgs):
        a: str
        b: Optional[int]
        c: Optional[int]
        list: List[str]

    def parse_args(args: List[str]) -> MyArgs:
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=str, required=True)
        parser.add_argument("--b", type=int)
        parser.add_argument("--c", type=int)
        parser.add_argument("--list", type=str, nargs="*")
        return MyArgs(parser.parse_args(args))

    args = parse_args(["--a", "a", "--c", "42"])
    expected = "MyArgs(a='a', b=None, c=42, list=[])"
    assert str(args) == expected
    assert repr(args) == expected


# -----------------------------------------------------------------------------
# Literal / Enum
# -----------------------------------------------------------------------------


def test_get_choices_from() -> None:
    class EnumInt(enum.Enum):
        a = 1
        b = 2
        c = 3

    assert get_choices_from(Literal[1, 2, 3]) == [1, 2, 3]
    assert get_choices_from(EnumInt) == [1, 2, 3]

    # Support list wrapping
    assert get_choices_from(List[Literal[1, 2, 3]]) == [1, 2, 3]
    assert get_choices_from(List[EnumInt]) == [1, 2, 3]


def test_get_choices_from_class() -> None:
    class EnumInt(enum.Enum):
        a = 1
        b = 2
        c = 3

    class EnumStr(enum.Enum):
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

    assert MyClass.get_choices_from("enum_int") == [1, 2, 3]
    assert MyClass.get_choices_from("enum_str") == ["a", "b", "c"]

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


def test_literal() -> None:
    class MyArgs(TypedArgs):
        foo: Literal[1, 2, 3]

    args_namespace = argparse.Namespace(foo=1)
    args = MyArgs(args_namespace)
    assert args.foo == 1

    args_namespace = argparse.Namespace(foo=4)
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'foo': "
        r"value 4 does not match any allowed literal value in \(1, 2, 3\)",
    ):
        MyArgs(args_namespace)


def test_enum() -> None:
    class EnumInt(enum.Enum):
        a = 1
        b = 2
        c = 3

    class MyArgs(TypedArgs):
        foo: EnumInt

    args_namespace = argparse.Namespace(foo=1)
    args = MyArgs(args_namespace)
    assert args.foo is EnumInt.a

    args_namespace = argparse.Namespace(foo=4)
    with pytest.raises(
        TypeError,
        match=r"Failed to validate argument 'foo': "
        r"value 4 does not match any allowed enum value in "
        r"\(<EnumInt.a: 1>, <EnumInt.b: 2>, <EnumInt.c: 3>\)",
    ):
        MyArgs(args_namespace)


# -----------------------------------------------------------------------------
# WithUnionType
# -----------------------------------------------------------------------------


def test_with_union_type() -> None:
    class Foo(TypedArgs):
        mode: Literal["foo"]

    class Bar(TypedArgs):
        mode: Literal["bar"]

    Args = Union[Foo, Bar]

    args_namespace = argparse.Namespace(mode="foo")
    args = WithUnionType[Args].validate(args_namespace)
    assert isinstance(args, Foo)

    args_namespace = argparse.Namespace(mode="bar")
    args = WithUnionType[Args].validate(args_namespace)
    assert isinstance(args, Bar)

    # No type of Union matching
    args_namespace = argparse.Namespace(mode="illegal")
    with pytest.raises(TypeError) as e:
        WithUnionType[Args].validate(args_namespace)
    expected = (
        "Validation failed against all sub types of union type:\n"
        " - Failed to validate argument 'mode': "
        "value illegal does not match any allowed literal value in ('foo',)\n"
        " - Failed to validate argument 'mode': "
        "value illegal does not match any allowed literal value in ('bar',)"
    )
    print(repr(str(e.value)))
    print(repr(expected))
    assert str(e.value) == expected

    # Illegal Union
    args_namespace = argparse.Namespace()
    with pytest.raises(TypeError) as e:
        WithUnionType[Union[str, int]].validate(args_namespace)
    expected = f"Type union {Union[str, int]} did not contain any sub types of type TypedArgs."
    print(repr(str(e.value)))
    print(repr(expected))
    assert str(e.value) == expected


# -----------------------------------------------------------------------------
# Mutually exclusive group
# -----------------------------------------------------------------------------


def test_mutually_exclusive_group() -> None:
    class Foo(TypedArgs):
        foo: str

    class Bar(TypedArgs):
        bar: str

    Args = Union[Foo, Bar]

    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--foo")
    g.add_argument("--bar")

    args = WithUnionType[Args].validate(parser.parse_args(["--foo", "foo"]))
    assert isinstance(args, Foo)
    assert args.foo == "foo"

    args = WithUnionType[Args].validate(parser.parse_args(["--bar", "bar"]))
    assert isinstance(args, Bar)
    assert args.bar == "bar"


# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------


def test_get_raw_args() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.get_raw_args().foo == "foo"


def test_get_raw_args__check_for_name_collision_1() -> None:
    class MyArgs(TypedArgs):
        get_raw_args: str  # type: ignore   # error on purpose for testing

    args_namespace = argparse.Namespace(get_raw_args="foo")
    with pytest.raises(
        TypeError,
        match="A type must not have an argument called 'get_raw_args'",
    ):
        MyArgs(args_namespace)


def test_get_raw_args__check_for_name_collision_2() -> None:
    class MyArgs(TypedArgs):
        _args: str  # type: ignore   # error on purpose for testing

    args_namespace = argparse.Namespace(get_raw_args="foo")
    with pytest.raises(
        TypeError,
        match="A type must not have an argument called '_args'",
    ):
        MyArgs(args_namespace)
