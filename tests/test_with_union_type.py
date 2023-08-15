import argparse
from typing import Literal, Union

import pytest

from typed_argparse import TypedArgs, WithUnionType

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
