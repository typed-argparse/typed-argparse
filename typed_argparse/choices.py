from typing import Any, List

from .type_utils import RawTypeAnnotation, TypeAnnotation, assert_not_none, typename


class Choices(List[Any]):
    """
    Work-around for Python bug: https://bugs.python.org/issue27227

    Inspired by: https://bugs.python.org/issue9625#msg347742
    """

    def __new__(cls, *args: object) -> "Choices":
        x = list.__new__(cls, *args)
        return x

    def __init__(self, *args: object) -> None:
        super().__init__(args)

    def __contains__(self, item_or_items: object) -> bool:
        # Notes:
        # - When argparse passes in the args that are externally specified,
        #   they get passed in one-by-one, i.e., item_or_items is a single element.
        #   Argparse internally collects the elements into a list.
        # - When argparse passes in the `default` value, it is passed in as is.
        #   Argparse doesn't collect multiple elements into a list in this case.
        #   Since the __contains__ function can only return whether this passed
        #   in default is valid, all we can do is to iterate over its contents
        #   and check them against the allowed values. If all are valid, we
        #   return True, so that the default value gets accepted. Note that it
        #   is crucial that the passed in default is a list/tuple. If it is a
        #   single element, we have to accept it as well due to the single
        #   element handling of externally passed in values, and there is no way
        #   to detect the default isn't a list.

        if isinstance(item_or_items, list) or isinstance(item_or_items, tuple):
            items = item_or_items
        else:
            items = [item_or_items]

        return all(list.__contains__(self, item) for item in items)


def get_choices_from_class(cls: type, field: str) -> Choices:
    """
    Helper function to extract allowed values from class field (which is a literal/enum like).

    Use case: Forward as `choices=...` argument to argparse.
    """
    if field in cls.__annotations__:
        raw_type_annotation: RawTypeAnnotation = cls.__annotations__[field]
        try:
            return get_choices_from(raw_type_annotation)
        except TypeError as e:
            raise TypeError(
                f"Could not infer literal values of field '{field}' "
                f"of type {typename(raw_type_annotation)}"
            ) from e
    else:
        raise TypeError(f"Class {cls.__name__} doesn't have a type annotation for field '{field}'")


def get_choices_from(raw_type_annotation: RawTypeAnnotation) -> Choices:
    """
    Helper function to extract allowed values from a literal/enum like type.

    Use case: Forward as `choices=...` argument to argparse.
    """
    type_annotation = TypeAnnotation(raw_type_annotation)

    while type_annotation.get_underlying_if_list() is not None:
        type_annotation = assert_not_none(type_annotation.get_underlying_if_list())

    allowed_values = type_annotation.get_allowed_values_if_literal()
    if allowed_values is not None:
        return Choices(*allowed_values)

    allowed_values = type_annotation.get_allowed_values_if_enum()
    if allowed_values is not None:
        return Choices(*allowed_values)

    raise TypeError(f"Could not infer literal values of type {typename(raw_type_annotation)}")
