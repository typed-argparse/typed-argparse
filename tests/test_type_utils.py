from typed_argparse import type_utils

from typing import List, Optional


def test_is_list() -> None:
    assert not type_utils.is_list(int)
    assert not type_utils.is_list(str)
    assert type_utils.is_list(List[str])
    assert type_utils.is_list(List[int])


def test_get_underlying_type_of_list() -> None:
    assert type_utils.get_underlying_type_of_list(List[str]) == str
    assert type_utils.get_underlying_type_of_list(List[int]) == int


def test_is_optional() -> None:
    assert not type_utils.is_optional(int)
    assert not type_utils.is_optional(str)
    assert type_utils.is_optional(Optional[str])
    assert type_utils.is_optional(Optional[int])


def test_get_underlying_type_of_optional() -> None:
    assert type_utils.get_underlying_type_of_optional(Optional[str]) == str
    assert type_utils.get_underlying_type_of_optional(Optional[int]) == int
