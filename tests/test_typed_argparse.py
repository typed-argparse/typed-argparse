from typed_argparse import TypedArgs

import argparse
import pytest


def test_basic() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"


def test_field_missing__single() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace()
    with pytest.raises(TypeError, match="Arguments object is missing attribute 'foo'"):
        MyArgs(args_namespace)


def test_field_missing__multiple() -> None:
    class MyArgs(TypedArgs):
        foo: str
        bar: str

    args_namespace = argparse.Namespace()
    with pytest.raises(TypeError, match=r"Arguments object is missing attributes \['foo', 'bar'\]"):
        MyArgs(args_namespace)
