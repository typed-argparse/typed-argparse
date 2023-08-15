from typing import Type, TypeVar, overload

import pytest

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


@pytest.mark.skip(reason="doesn't work yet")
def test_constructor__invalid_cases() -> None:
    class Args(TypedArgs):
        a: int
        b: str

    with pytest.raises(ValueError):
        Args()  # type: ignore[call-arg]


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
