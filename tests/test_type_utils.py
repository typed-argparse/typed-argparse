from typed_argparse import type_utils

from typing import List, Optional, Union


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
