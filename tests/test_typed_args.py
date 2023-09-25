import argparse
from typing import List, Optional, Type, TypeVar, overload

import typed_argparse as tap
from typed_argparse import TypedArgs

# -----------------------------------------------------------------------------
# Constructor type safety
# -----------------------------------------------------------------------------

T = TypeVar("T")


@overload
def assert_type(x: int, type_: Type[int], ignore: bool = ...) -> None:
    ...


@overload
def assert_type(x: str, type_: Type[str], ignore: bool = ...) -> None:
    ...


def assert_type(x: T, type_: Type[T], ignore: bool = False) -> None:
    if not ignore:
        assert isinstance(x, type_)


def test_constructor__basics() -> None:
    class Args(TypedArgs):
        a: int
        b: str

    instance = Args(a=42, b="s")
    assert instance.a == 42
    assert instance.b == "s"
    assert instance.__dict__ == {"a": 42, "b": "s"}

    assert_type(instance.a, int)
    assert_type(instance.b, str)

    assert_type(instance.a, str, ignore=True)  # type: ignore
    assert_type(instance.b, int, ignore=True)  # type: ignore


def test_constructor__inheritance() -> None:
    class BaseArgs(TypedArgs):
        a: int

    class Args(BaseArgs):
        b: str

    instance = Args(a=42, b="s")
    assert instance.a == 42
    assert instance.b == "s"
    assert instance.__dict__ == {"a": 42, "b": "s"}

    assert_type(instance.a, int)
    assert_type(instance.b, str)

    assert_type(instance.a, str, ignore=True)  # type: ignore
    assert_type(instance.b, int, ignore=True)  # type: ignore


def test_constructor__invalid_cases() -> None:
    class Args(TypedArgs):
        a: int
        b: str

    Args()  # type: ignore[call-arg]
    Args(a=42)  # type: ignore[call-arg]
    Args(b="s")  # type: ignore[call-arg]
    Args(
        a="s",  # type: ignore[arg-type]
        b=42,  # type: ignore[arg-type]
    )
    Args(
        a=42,
        b="s",
        additional=True,  # type: ignore[call-arg]
    )


def test_constructor__invalid_cases__annotated() -> None:
    class Args(TypedArgs):
        a: int = tap.arg()
        b: str = tap.arg()

    Args(a=42)  # type: ignore[call-arg]
    Args(b="s")  # type: ignore[call-arg]
    Args(
        a="s",  # type: ignore[arg-type]
        b=42,  # type: ignore[arg-type]
    )
    Args(
        a=42,
        b="s",
        additional=True,  # type: ignore[call-arg]
    )


def test_constructor__inheritance__invalid_cases() -> None:
    class BaseArgs(TypedArgs):
        a: int

    class Args(BaseArgs):
        b: str

    Args()  # type: ignore[call-arg]
    Args(a=42)  # type: ignore[call-arg]
    Args(b="s")  # type: ignore[call-arg]
    Args(
        a="s",  # type: ignore[arg-type]
        b=42,  # type: ignore[arg-type]
    )
    Args(
        a=42,
        b="s",
        additional=True,  # type: ignore[call-arg]
    )


def test_constructor__inheritance__invalid_cases__annotated() -> None:
    class BaseArgs(TypedArgs):
        a: int = tap.arg()

    class Args(BaseArgs):
        b: str = tap.arg()

    Args()  # type: ignore[call-arg]
    Args(a=42)  # type: ignore[call-arg]
    Args(b="s")  # type: ignore[call-arg]
    Args(
        a="s",  # type: ignore[arg-type]
        b=42,  # type: ignore[arg-type]
    )
    Args(
        a=42,
        b="s",
        additional=True,  # type: ignore[call-arg]
    )


# -----------------------------------------------------------------------------
# Constructor defaults handling
# -----------------------------------------------------------------------------


def test_constructor__defaults__basic() -> None:
    class Args(TypedArgs):
        a: int = tap.arg(default=42)

    instance = Args()
    assert instance.a == 42

    instance = Args(a=43)
    assert instance.a == 43


def test_constructor__defaults__inheritance() -> None:
    class Parent(TypedArgs):
        foo: str = tap.arg(default="foo")

    class Child(Parent):
        bar: str = tap.arg(default="bar")

    instance = Child()
    assert instance.foo == "foo"
    assert instance.bar == "bar"

    instance = Child(foo="foo_custom")
    assert instance.foo == "foo_custom"
    assert instance.bar == "bar"

    instance = Child(bar="bar_custom")
    assert instance.foo == "foo"
    assert instance.bar == "bar_custom"

    instance = Child(foo="foo_custom", bar="bar_custom")
    assert instance.foo == "foo_custom"
    assert instance.bar == "bar_custom"


def test_constructor__defaults__plain_values() -> None:
    class Args(TypedArgs):
        a: int = 42

    instance = Args()
    assert instance.a == 42

    instance = Args(a=43)
    assert instance.a == 43


def test_constructor__defaults__plain_values__deep_copy() -> None:
    # This is a bit pathological. Should plain attributes get deep copied?

    singleton = [1, 2, 3]

    class Args(TypedArgs):
        a: List[int] = singleton

    instance = Args()
    assert instance.a == singleton
    assert instance.a is not singleton

    instance = Args(a=[2, 3, 4])
    assert instance.a == [2, 3, 4]


def test_constructor__defaults__nargs__deep_copy() -> None:
    singleton = [1, 2, 3]

    class Args(TypedArgs):
        a: List[int] = tap.arg(default=singleton)

    instance = Args()
    assert instance.a == singleton
    assert instance.a is not singleton

    instance = Args(a=[2, 3, 4])
    assert instance.a == [2, 3, 4]


def test_constructor__defaults__separated_argument_definition() -> None:
    reusable_arg = tap.arg(default=42)

    class Args(TypedArgs):
        a: int = reusable_arg

    instance = Args()
    assert instance.a == 42

    instance = Args(a=43)
    assert instance.a == 43


def test_constructor__defaults__optional() -> None:
    # TODO: Here it would be nice if the either `default=None` or the entire `tap.arg` expression
    # could be omitted.

    class Args(TypedArgs):
        a: Optional[int] = tap.arg(default=None)

    instance = Args()
    assert instance.a is None

    instance = Args(a=43)
    assert instance.a == 43


def test_constructor__defaults__bool_switches() -> None:
    # Similarly here, omitting the default values especially in the positive case would be nice.

    class Args(TypedArgs):
        positive: bool = tap.arg(default=True)
        negative: bool = tap.arg(default=False)

    instance = Args()
    assert instance.positive
    assert not instance.negative

    instance = Args(positive=False, negative=True)
    assert not instance.positive
    assert instance.negative


# -----------------------------------------------------------------------------
# __str__
# -----------------------------------------------------------------------------


def test_string_representation() -> None:
    class Args(TypedArgs):
        a: str
        b: Optional[int]
        c: Optional[int]
        list: List[str]

    def parse_args(args: List[str]) -> Args:
        parser = argparse.ArgumentParser()
        parser.add_argument("--a", type=str, required=True)
        parser.add_argument("--b", type=int)
        parser.add_argument("--c", type=int)
        parser.add_argument("--list", type=str, nargs="*")
        return Args.from_argparse(parser.parse_args(args))

    args = parse_args(["--a", "a", "--c", "42"])
    expected = "Args(a='a', b=None, c=42, list=[])"
    assert str(args) == expected
    assert repr(args) == expected


# -----------------------------------------------------------------------------
# __eq__
# -----------------------------------------------------------------------------


def test_eq_and_ne() -> None:
    class Args(TypedArgs):
        a: str
        b: int

    assert Args(a="foo", b=42) == Args(a="foo", b=42)
    assert Args(a="foo", b=42) != Args(a="foo", b=43)
    assert Args(a="foo", b=42) != 42


def test_eq__well_behaved() -> None:
    # Tests for proper __eq__ semantics when comparing with other types, see e.g.:
    # https://github.com/jwodder/anys#caveat-custom-classes

    class Args(TypedArgs):
        ...

    compared_objects = []

    class Other:
        def __eq__(self, other: object) -> bool:
            compared_objects.append(other)
            return False

    instance = Args()
    assert instance != Other()
    assert compared_objects == [instance]


# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------


def test_check_reserved_names() -> None:
    fields_class = set(TypedArgs.__dict__)
    assert fields_class == {
        "__dataclass_transform__",
        "__dict__",
        "__doc__",
        "__eq__",
        "__hash__",
        "__init__",
        "__module__",
        "__ne__",
        "__repr__",
        "__str__",
        "__weakref__",
        "from_argparse",
        "get_choices_from",
    }
