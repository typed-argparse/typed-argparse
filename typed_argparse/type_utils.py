import sys
from enum import Enum
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from typing_extensions import Literal

_NoneType = type(None)


# It looks like there is no good type annotation that works for "type annotations".
# `type` would work for internal types (int, str, ...) and some typing.XXX types
# like typing.List and typing.Dict, but it doesn't work for typing.Optional and
# typing.Union. For now, let's make no assumptions at all.
RawTypeAnnotation = object


def collect_type_annotations(
    cls: type,
    *,
    include_super_types: bool = True,
) -> Dict[str, "TypeAnnotation"]:
    if include_super_types:
        return _collect_all_type_annotations(cls)

    else:
        own_annotations = _collect_all_type_annotations(cls)

        types = cls.mro()
        if len(types) > 1:
            parent_annotations = _collect_all_type_annotations(types[1])
            return {k: v for k, v in own_annotations.items() if k not in parent_annotations}
        else:
            return own_annotations


def _collect_all_type_annotations(cls: type) -> Dict[str, "TypeAnnotation"]:
    return {name: TypeAnnotation(annotation) for name, annotation in get_type_hints(cls).items()}


def typename(t: RawTypeAnnotation) -> str:
    if hasattr(t, "__name__"):
        return f"'{getattr(t, '__name__')}'"
    else:
        return f"'{str(t)}'"


def typename_of(value: object) -> str:
    return typename(type(value))


def _get_origin(t: RawTypeAnnotation) -> Optional[RawTypeAnnotation]:
    return cast(Optional[object], getattr(t, "__origin__", None))


def _get_args(t: RawTypeAnnotation) -> Tuple[RawTypeAnnotation, ...]:
    args = getattr(t, "__args__", ())
    if not isinstance(args, tuple):
        raise TypeError(
            f"Expected __args__ of type annotation to be a tuple, but it is {type(args)}"
        )
    return args


class TypeAnnotation:
    def __init__(self, raw_type: RawTypeAnnotation):
        self.raw_type: RawTypeAnnotation = raw_type
        self.origin = _get_origin(raw_type)
        self.args = _get_args(raw_type)

    @property
    def is_bool(self) -> bool:
        return self.raw_type is bool

    def get_underlying_type_converter(self) -> Optional[Union[type, Callable[[str], object]]]:
        if isinstance(self.raw_type, type) and not issubclass(self.raw_type, Enum):
            return self.raw_type
        else:
            underlying = self.get_underlying_if_optional()
            if underlying is not None:
                return underlying.get_underlying_type_converter()
            underlying = self.get_underlying_if_list()
            if underlying is not None:
                return underlying.get_underlying_type_converter()

            allowed_values_if_literal = self.get_allowed_values_if_literal()
            if allowed_values_if_literal is not None:
                allowed_values = allowed_values_if_literal
                return _create_literal_type_converter(allowed_values)

            allowed_values_if_enum = self.get_allowed_values_if_enum()
            if (
                allowed_values_if_enum is not None
                and isinstance(self.raw_type, type)
                and issubclass(self.raw_type, Enum)
            ):
                allowed_values = allowed_values_if_enum
                enum_type: Type[Enum] = self.raw_type
                return _create_enum_type_converter(allowed_values, enum_type)

            return None

    def get_underlying_if_optional(self) -> Optional["TypeAnnotation"]:
        if self.origin is Union and len(self.args) == 2 and _NoneType in self.args:
            for t in self.args:
                if t != _NoneType:
                    return TypeAnnotation(t)
        return None

    def get_underlying_if_list(self) -> Optional["TypeAnnotation"]:
        # In Python 3.6 __origin__ is List
        # In Python 3.7+ __origin__ is list
        if (self.origin is List or self.origin is list) and len(self.args) >= 1:
            return TypeAnnotation(self.args[0])
        return None

    def get_underlying_if_new_type(self) -> Optional["TypeAnnotation"]:
        # Using the same heuristic as pydantic: https://github.com/pydantic/pydantic/pull/223/files
        if hasattr(self.raw_type, "__name__") and hasattr(self.raw_type, "__supertype__"):
            return TypeAnnotation(getattr(self.raw_type, "__supertype__"))
        return None

    def get_underlyings_if_union(self) -> List["TypeAnnotation"]:
        if self.origin is Union:
            return [TypeAnnotation(t) for t in self.args]
        else:
            return []

    def get_allowed_values_if_literal(self) -> Optional[Tuple[object, ...]]:
        if sys.version_info[:2] == (3, 6):
            # In Python 3.6 Literal must come from typing_extensions. However, it does not
            # behave like other generics, and proper instance checking doesn't seem to work.
            # We use the simple heuristic to look for __values__ directly without any instance
            # checks.
            if hasattr(self.raw_type, "__values__"):
                values = getattr(self.raw_type, "__values__")
                if isinstance(values, tuple):
                    return values
            return None

        elif sys.version_info[:2] >= (3, 7):
            # In Python 3.7 Literal must come from typing_extensions. In contrast to Python 3.6
            # it uses typing._GenericAlias and __args__ similar to other generics. This makes
            # it necessary to properly detect literal instance.
            # In Python 3.8+, Literal has been integrated into typing itself.
            # Using the import from typing_extensions should make it work in both cases.
            if self.origin is Literal:
                return self.args
            else:
                return None

        else:
            raise AssertionError(f"Python version {sys.version_info} is not supported")

    def get_allowed_values_if_enum(self) -> Optional[Tuple[Enum, ...]]:
        if isinstance(self.raw_type, type) and issubclass(self.raw_type, Enum):
            return tuple(self.raw_type)
        else:
            return None

    def validate(self, value: object) -> Tuple[object, Optional[str]]:

        # Handle optionals
        underlying_if_optional = self.get_underlying_if_optional()
        if underlying_if_optional is not None:
            if value is None:
                return None, None
            else:
                return underlying_if_optional.validate(value)

        # Handle unions
        underlyings_if_union = self.get_underlyings_if_union()
        if len(underlyings_if_union) > 0:
            errors: List[str] = []
            for underlying in underlyings_if_union:
                new_value, error = underlying.validate(value)
                if error is None:
                    return new_value, None
                else:
                    errors.append(error)
            return (
                value,
                f"value {value} did not match any type of union:\n - " + "\n - ".join(errors),
            )

        # Handle lists
        underlying_if_list = self.get_underlying_if_list()
        if underlying_if_list is not None:
            if value is None:
                # Coerce empty list.
                return [], None
            elif not isinstance(value, list):
                # allowing isinstance(value, Iterable) seems too lose, because it would allow
                # to coerce a list from string, which is not desirable.
                return value, f"value is of type {typename_of(value)}, expected 'list'"
            else:
                new_values = []
                for x in value:
                    new_value, error = underlying_if_list.validate(x)
                    if error is not None:
                        return value, f"not all elements of the list have proper type ({error})"
                    new_values.append(new_value)
                return new_values, None

        # Handle literals
        allowed_values_if_literal = self.get_allowed_values_if_literal()
        if allowed_values_if_literal is not None:
            for allowed_value in allowed_values_if_literal:
                if value == allowed_value:
                    return value, None
            return (
                value,
                f"value {value} does not match any allowed literal value in "
                f"{allowed_values_if_literal}",
            )

        # Handle enums
        allowed_values_if_enum = self.get_allowed_values_if_enum()
        if allowed_values_if_enum is not None:
            for allowed_value in allowed_values_if_enum:
                if value == allowed_value.value:
                    return allowed_value, None
                elif value is allowed_value:
                    return allowed_value, None
            return (
                value,
                f"value {value} does not match any allowed enum value in "
                f"{allowed_values_if_enum}",
            )

        # Handle new type
        underlying_if_new_type = self.get_underlying_if_new_type()
        if underlying_if_new_type is not None:
            return underlying_if_new_type.validate(value)

        # We have to assert self.raw_type is a true `type`
        if not isinstance(self.raw_type, type):
            return (
                value,
                f"Type annotation is of type {typename_of(self.raw_type)}, expected 'type'",
            )

        if isinstance(value, self.raw_type):
            return value, None
        else:
            return (
                value,
                f"value is of type {typename_of(value)}, expected {typename(self.raw_type)}",
            )

    def validate_with_error(
        self,
        value: object,
        arg_name: str,
    ) -> object:

        value, error = self.validate(value)

        if error is not None:
            raise TypeError(f"Failed to validate argument '{arg_name}': {error}")

        return value


T = TypeVar("T")


def assert_not_none(x: Optional[T]) -> T:
    assert x is not None
    return x


def _create_literal_type_converter(allowed_values: Tuple[object, ...]) -> Callable[[str], object]:
    def converter(x: str) -> object:

        for allowed_value in allowed_values:
            if _fuzzy_compare(x, allowed_value):
                return allowed_value
            else:
                try:
                    x_converted = type(allowed_value)(x)  # type: ignore
                    if _fuzzy_compare(x_converted, allowed_value):
                        return allowed_value
                except (ValueError, TypeError):
                    pass

        # Here we could raise a TypeError or ValueError, but it looks like relying
        # on `choices` instead actually produces a better error message.
        return x

    return converter


def _create_enum_type_converter(
    allowed_values: Tuple[Enum, ...], enum_type: Type[Enum]
) -> Callable[[str], object]:
    def converter(x: str) -> object:

        for allowed_value in allowed_values:
            assert isinstance(allowed_value, Enum)
            if _fuzzy_compare(x, allowed_value.name):
                return allowed_value
            else:
                if _fuzzy_compare(x, allowed_value.value):
                    return allowed_value
                else:
                    try:
                        x_converted = type(allowed_value.value)(x)
                        if _fuzzy_compare(x_converted, allowed_value.value):
                            return allowed_value
                    except (ValueError, TypeError):
                        pass

        # Here we could raise a TypeError or ValueError, but it looks like relying
        # on `choices` instead actually produces a better error message.
        return x

    return converter


def _fuzzy_compare(a: object, b: object) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a.lower().replace("-", "_") == b.lower().replace("-", "_")
    else:
        return a == b
