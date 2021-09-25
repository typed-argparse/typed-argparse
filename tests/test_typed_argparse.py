from typed_argparse import TypedArgs

import argparse
import pytest

from typing import List, Optional, Union


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
        match=r"Arguments object has an unexpected extra arguments \['bar', 'baz'\]",
    ):
        MyArgs(args_namespace)


def test_simple_type_mismatch_1() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError,
        match="Type of argument 'foo' should be str, but is int",
    ):
        MyArgs(args_namespace)


def test_simple_type_mismatch_2() -> None:
    class MyArgs(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num="foo")
    with pytest.raises(
        TypeError,
        match="Type of argument 'num' should be int, but is str",
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
        match="Not all elements of argument 'foo' are of type str",
    ):
        MyArgs(args_namespace)


def test_lists__elements_type_mismatch_2() -> None:
    class MyArgs(TypedArgs):
        num: List[int]

    args_namespace = argparse.Namespace(num=["a", 2, "c"])
    with pytest.raises(
        TypeError,
        match="Not all elements of argument 'num' are of type int",
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
        TypeError,
        match=r"Type of argument 'foo' should be Optional\[str\], but is int",
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


# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------


def test_get_raw_args() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.get_raw_args().foo == "foo"


def test_get_raw_args__check_for_name_collision() -> None:
    class MyArgs(TypedArgs):
        get_raw_args: str  # type: ignore   # error on purpose for testing

    args_namespace = argparse.Namespace(get_raw_args="foo")
    with pytest.raises(
        TypeError,
        match="A type must not have an argument called 'get_raw_args'",
    ):
        MyArgs(args_namespace)
