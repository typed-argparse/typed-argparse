import argparse

import inspect
import typing
from typing import Any, Dict, List, Tuple, TypeVar, Generic

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

        # Collect all annotations (including super types)
        all_annotations: Dict[str, object] = dict()
        for cls in reversed(type(self).mro()):
            if hasattr(cls, "__annotations__"):
                all_annotations.update(**cls.__annotations__)

        for arg_name, type_annotation_any in all_annotations.items():
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
        extra_args = sorted(set(args.__dict__.keys()) - set(all_annotations.keys()))
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


T = TypeVar("T")

# It may seem natural to use a generic signature for this function to return the
# type corresponding to the specified union type like:
#
#     def validate_type_union(type_union: Type[T], args: argparse.Namespace) -> T:
#
# However, that doesn't work currently, because of limitations of Union and Type[T].
# See: https://github.com/python/mypy/issues/9003


def validate_type_union(args: argparse.Namespace, type_union: object) -> object:
    """
    Helper function to validate args against a type union (but with untyped return).
    """
    type_annotation = TypeAnnotation(type_union)

    errors = []

    for sub_type in type_annotation.get_underlyings_if_union():
        if isinstance(sub_type.raw_type, type) and issubclass(sub_type.raw_type, TypedArgs):
            try:
                return sub_type.raw_type(args)  # type: ignore
            except Exception as e:
                errors.append(str(e))

    if len(errors) == 0:
        raise TypeError(f"Type union {type_union} did not contain any sub types of type TypedArgs.")
    else:
        errors_str = "\n - ".join(errors)
        raise TypeError(f"Validation failed against all sub types of union type:\n{errors_str}")


# Workaround for generic type erasure:
# https://github.com/python/typing/issues/629#issuecomment-829629259


class Proxy:
    def __init__(self, generic: Any) -> None:
        object.__setattr__(self, "_generic", generic)

    def __getattr__(self, name: str) -> Any:
        if typing._is_dunder(name):  # type: ignore # noqa
            return getattr(self._generic, name)
        origin = self._generic.__origin__
        obj = getattr(origin, name)
        if inspect.ismethod(obj) and isinstance(obj.__self__, type):
            return lambda *a, **kw: obj.__func__(self, *a, *kw)
        else:
            return obj

    def __setattr__(self, name: str, value: Any) -> Any:
        return setattr(self._generic, name, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._generic.__call__(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} of {self._generic!r}>"


class RuntimeGeneric:
    def __class_getitem__(cls: Any, key: str) -> Any:
        generic = super().__class_getitem__(key)  # type: ignore
        if getattr(generic, "__origin__", None):
            return Proxy(generic)
        else:
            return generic


class WithUnionType(RuntimeGeneric, Generic[T]):
    """
    Helper class to validate args against a type union (with proper return type).
    """

    @classmethod
    def validate(cls, args: argparse.Namespace) -> T:
        generic_args = TypeAnnotation(cls).args
        if len(generic_args) != 1:
            raise TypeError(
                f"Class needs exactly one generic annotation. Annotations are {generic_args}."
            )
        return validate_type_union(args, generic_args[0])  # type: ignore
