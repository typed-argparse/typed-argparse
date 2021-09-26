import argparse

from typing import Any, List, Tuple

from .type_utils import RawTypeAnnotation, TypeAnnotation, typename, validate_value_against_type

_NoneType = type(None)


class TypedArgs:
    def __init__(self, args: argparse.Namespace) -> None:
        """
        Constructs an instance of the TypedArgs class from a given argparse Namespace.

        Performs various validations / sanity check to make sure the runtime values
        match the type annotations.
        """
        self._args = args

        missing_args: List[str] = []

        for arg_name, type_annotation_any in self.__annotations__.items():
            if arg_name == "get_raw_args" or arg_name == "_args":
                raise TypeError(f"A type must not have an argument called '{arg_name}'")

            type_annotation: RawTypeAnnotation = type_annotation_any

            if hasattr(args, arg_name):
                # Validate the value and add as attribute
                value: object = getattr(args, arg_name)
                value = validate_value_against_type(
                    arg_name,
                    value,
                    type_annotation,
                )
                self.__dict__[arg_name] = value
            else:
                missing_args.append(arg_name)

        # Report missing args if any
        if len(missing_args) > 0:
            if len(missing_args) == 1:
                raise TypeError(f"Arguments object is missing argument '{missing_args[0]}'")
            else:
                raise TypeError(f"Arguments object is missing arguments {missing_args}")

        # Report extra args if any
        extra_args = sorted(set(args.__dict__.keys()) - set(self.__annotations__.keys()))
        if len(extra_args) > 0:
            if len(extra_args) == 1:
                raise TypeError(
                    f"Arguments object has an unexpected extra argument '{extra_args[0]}'"
                )
            else:
                raise TypeError(f"Arguments object has unexpected extra arguments {extra_args}")

    def get_raw_args(self) -> argparse.Namespace:
        """
        Access to the raw argparse namespace if needed.
        """
        return self._args

    def __repr__(self) -> str:
        key_value_pairs = [f"{k}={repr(v)}" for k, v in self.__dict__.items() if k != "_args"]
        return f"{self.__class__.__name__}({', '.join(key_value_pairs)})"

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def get_choices_from(cls: type, field: str) -> Tuple[Any, ...]:
        """
        Helper function to extra allowed values from a Literal/Enum. Use case:
        Forward as `choices=...` argument to argparse.
        """
        return get_choices_from(cls, field)


def get_choices_from(cls: type, field: str) -> Tuple[Any, ...]:
    """
    Helper function to extra allowed values from a Literal/Enum. Use case:
    Forward as `choices=...` argument to argparse.
    """
    if field in cls.__annotations__:
        raw_type_annotation: RawTypeAnnotation = cls.__annotations__[field]
        type_annotation = TypeAnnotation(raw_type_annotation)

        allowed_values = type_annotation.get_allowed_values_if_literal()
        if allowed_values is not None:
            return allowed_values

        allowed_values = type_annotation.get_allowed_values_if_enum()
        if allowed_values is not None:
            return tuple(e.value for e in allowed_values)

        raise TypeError(
            f"Could not infer literal values of field '{field}' "
            f"of type {typename(raw_type_annotation)}"
        )

    else:
        raise TypeError(f"Class {cls.__name__} doesn't have a type annotation for field '{field}'")
