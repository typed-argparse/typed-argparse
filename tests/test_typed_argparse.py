from typed_argparse import TypedArgs

import argparse
import pytest


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
        match="Arguments object is missing attribute 'foo'",
    ):
        MyArgs(args_namespace)


def test_missing_field__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str
        bar: str

    args_namespace = argparse.Namespace()
    with pytest.raises(
        TypeError,
        match=r"Arguments object is missing attributes \['foo', 'bar'\]",
    ):
        MyArgs(args_namespace)


def test_extra_field__single() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar")
    with pytest.raises(
        TypeError,
        match="Arguments object has an unexpected extra attribute 'bar'",
    ):
        MyArgs(args_namespace)


def test_extra_field__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo", bar="bar", baz="baz")
    with pytest.raises(
        TypeError,
        match=r"Arguments object has an unexpected extra attributes \['bar', 'baz'\]",
    ):
        MyArgs(args_namespace)


def test_simple_type_mismatch_1() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo=42)
    with pytest.raises(
        TypeError,
        match="Type of attribute 'foo' should be str, but is int",
    ):
        MyArgs(args_namespace)


def test_simple_type_mismatch_2() -> None:
    class MyArgs(TypedArgs):
        num: int

    args_namespace = argparse.Namespace(num="foo")
    with pytest.raises(
        TypeError,
        match="Type of attribute 'num' should be int, but is str",
    ):
        MyArgs(args_namespace)
