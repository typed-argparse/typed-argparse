from typed_argparse import type_utils

from typing import List, Optional


def test_is_list() -> None:
    assert not type_utils._is_list(int)
    assert not type_utils._is_list(str)
    assert type_utils._is_list(List[str])
    assert type_utils._is_list(List[int])
    # support for optional wrapping
    assert not type_utils._is_list(Optional[str])
    assert type_utils._is_list(Optional[List[str]])
    assert type_utils._is_list(Optional[Optional[Optional[List[str]]]])


def test_get_underlying_type_of_list() -> None:
    assert type_utils._get_underlying_type_of_list(List[str]) == str
    assert type_utils._get_underlying_type_of_list(List[int]) == int
    # support for optional wrapping
    assert type_utils._get_underlying_type_of_list(Optional[List[str]]) == str
    assert type_utils._get_underlying_type_of_list(Optional[Optional[Optional[List[str]]]]) == str


def test_is_optional() -> None:
    assert not type_utils._is_optional(int)
    assert not type_utils._is_optional(str)
    assert type_utils._is_optional(Optional[str])
    assert type_utils._is_optional(Optional[int])
    # arbitrary nesting
    assert type_utils._is_optional(Optional[Optional[Optional[int]]])


def test_get_underlying_type_of_optional() -> None:
    assert type_utils._get_underlying_type_of_optional(Optional[str]) == str
    assert type_utils._get_underlying_type_of_optional(Optional[int]) == int
    # arbitrary nesting
    assert type_utils._get_underlying_type_of_optional(Optional[Optional[Optional[int]]]) == int
