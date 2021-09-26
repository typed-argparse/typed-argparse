from typed_argparse import TypedArgs

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
        MyArgs(args_namespace)


def test_extra_field__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar", baz="baz")
    with pytest.raises(
        TypeError,
        match=r"Arguments object has unexpected extra arguments \['bar', 'baz'\]",
    ):
        MyArgs(args_namespace)


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


def test_get_choices_from() -> None:
    class MyClass(TypedArgs):
        a: Literal[1, 2, 3]
        b: Literal["a", "b", "c"]
        c: int

    assert MyClass.get_choices_from("a") == (1, 2, 3)
    assert MyClass.get_choices_from("b") == ("a", "b", "c")

    with pytest.raises(
        TypeError,
        match="Could not infer literal values of type annotation <class 'int'>",
    ):
        MyClass.get_choices_from("c")

    with pytest.raises(
        TypeError,
        match="Class MyClass doesn't have a type annotation for field 'non_existing'",
    ):
        MyClass.get_choices_from("non_existing")
