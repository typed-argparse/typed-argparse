from typing import List, Optional, Union

from typed_argparse import type_utils
from typed_argparse.type_utils import TypeAnnotation


def test_is_optional() -> None:
    assert not type_utils._is_optional(int)
    assert not type_utils._is_optional(str)
    assert type_utils._is_optional(Optional[str])
    assert type_utils._is_optional(Optional[int])
    # Arbitrary nesting
    assert type_utils._is_optional(Optional[Optional[Optional[int]]])
    # Support optionals that are expressed as Union explicitly
    assert type_utils._is_optional(Union[str, None])
    assert type_utils._is_optional(Union[None, str])
    # Don't confuse Union types with Optionals (which are Union[T, NoneType] internally)
    assert not type_utils._is_optional(Union[str, int])


def test_get_underlying_type_of_optional() -> None:
    assert type_utils._get_underlying_type_of_optional(Optional[str]) == str
    assert type_utils._get_underlying_type_of_optional(Optional[int]) == int
    # Arbitrary nesting
    assert type_utils._get_underlying_type_of_optional(Optional[Optional[Optional[int]]]) == int
    # Support optionals that are expressed as Union explicitly
    assert type_utils._get_underlying_type_of_optional(Union[str, None]) == str
    assert type_utils._get_underlying_type_of_optional(Union[None, str]) == str


def test_is_list() -> None:
    assert not type_utils._is_list(int)
    assert not type_utils._is_list(str)
    assert type_utils._is_list(List[str])
    assert type_utils._is_list(List[int])
    # Support for optional wrapping
    assert not type_utils._is_list(Optional[str])
    assert type_utils._is_list(Optional[List[str]])
    assert type_utils._is_list(Optional[Optional[Optional[List[str]]]])


def test_get_underlying_type_of_list() -> None:
    assert type_utils._get_underlying_type_of_list(List[str]) == str
    assert type_utils._get_underlying_type_of_list(List[int]) == int
    # Support for optional wrapping
    assert type_utils._get_underlying_type_of_list(Optional[List[str]]) == str
    assert type_utils._get_underlying_type_of_list(Optional[Optional[Optional[List[str]]]]) == str


# -----------------------------------------------------------------------------
# TypeAnnotation
# -----------------------------------------------------------------------------


def test_type_annotation__scalar_types() -> None:
    t = TypeAnnotation(str)
    assert t.origin is None
    assert t.args == ()
    assert t.get_underlying_if_optional() is None
    assert t.get_underlying_if_list() is None

    assert t.validate("foo") == ("foo", None)
    assert t.validate(12345) == (12345, "value is not of type str, but int")


def test_type_annotation__user_class() -> None:
    class MyClass:
        def __init__(self) -> None:
            self.a: int = 42
            self.b: str = "foo"

    t = TypeAnnotation(MyClass)
    assert t.origin is None
    assert t.args == ()
    assert t.get_underlying_if_optional() is None
    assert t.get_underlying_if_list() is None

    my_class = MyClass()
    assert t.validate(my_class) == (my_class, None)
    assert t.validate("foo") == ("foo", "value is not of type MyClass, but str")
    assert t.validate(12345) == (12345, "value is not of type MyClass, but int")


def test_type_annotation__optional() -> None:
    t = TypeAnnotation(Optional[str])
    t_underlying = t.get_underlying_if_optional()
    assert t_underlying is not None
    assert t_underlying.raw_type is str

    assert t.validate("foo") == ("foo", None)
    assert t.validate(None) == (None, None)


def test_type_annotation__list() -> None:
    t = TypeAnnotation(List[str])
    t_underlying = t.get_underlying_if_list()
    assert t_underlying is not None
    assert t_underlying.raw_type is str

    assert t.validate(["a", "b", "c"]) == (["a", "b", "c"], None)
    assert t.validate("foo") == ("foo", "value is not of type list, but str")


def test_type_annotation__mixed_list_optional() -> None:
    t = TypeAnnotation(Optional[List[str]]).get_underlying_if_optional()
    assert t is not None
    t = t.get_underlying_if_list()
    assert t is not None
    assert t.raw_type is str

    t = TypeAnnotation(List[Optional[str]]).get_underlying_if_list()
    assert t is not None
    t = t.get_underlying_if_optional()
    assert t is not None
    assert t.raw_type is str
