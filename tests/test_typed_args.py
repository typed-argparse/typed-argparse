import argparse
from typing import List, Optional, Type, TypeVar, overload

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
