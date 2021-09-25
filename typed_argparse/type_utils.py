from collections.abc import Iterable
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union, cast


_NoneType = type(None)


# It looks like there is no good type annotation that works for "type annotations".
# `type` would work for internal types (int, str, ...) and some typing.XXX types
# like typing.List and typing.Dict, but it doesn't work for typing.Optional and
# typing.Union. For now, let's make no assumptions at all.
TypeAnnotation = object


def _debug_repr(x: Any) -> Dict[str, Any]:
    return {name: getattr(x, name) for name in dir(x)}


def _is_generic_type(x: TypeAnnotation) -> bool:
    # Heuristic to detect generic types. Consider using a type guard for an even cleaner
    # approach at the cost of adding typing_extensions as a dependency.
    return hasattr(x, "__origin__")


class TypeWrapper:
    def __init__(self, name: str, validate: Callable[[object], bool]) -> None:
        self.name = name
        self.validate = validate


def get_type_wrapper(x: TypeAnnotation) -> TypeWrapper:
    # TODO: We could try to detect typing.Literal here, but it seems tricky:
    # https://stackoverflow.com/q/61150835/1804173
    if isinstance(x, type) or _is_generic_type(x):
        expected_type = cast(type, x)
        return TypeWrapper(
            name=getattr(x, "__name__", "unknown"),
            validate=lambda x: isinstance(x, expected_type),
        )
    else:
        raise TypeError(f"Type annotation must be a type, but is of type {type(x)}")


def validate_value_against_type(
    arg_name: str,
    value: object,
    type_annotation: TypeAnnotation,
) -> object:
    # Handle optional first to handle Optional[List[T]] properly
    optional_check = check_for_optional(type_annotation)
    if optional_check.is_optional:
        type_annotation = optional_check.underlying_type

    list_check = check_for_list(type_annotation)
    if list_check.is_list:
        type_annotation = list
        # Special handling for lists: Coerce empty lists automatically if not optional
        if value is None and not optional_check.is_optional:
            value = []

    type_wrapper = get_type_wrapper(type_annotation)

    if optional_check.is_optional:
        if not type_wrapper.validate(value) and not (value is None):
            raise TypeError(
                f"Type of argument '{arg_name}' should be "
                f"Optional[{type_wrapper.name}], but is "
                f"{type(value).__name__}"
            )

    else:
        if not type_wrapper.validate(value):
            raise TypeError(
                f"Type of argument '{arg_name}' should be "
                f"{type_wrapper.name}, but is "
                f"{type(value).__name__}"
            )

    if list_check.underlying_type is not None and isinstance(value, Iterable):
        if not all(isinstance(element, list_check.underlying_type) for element in value):
            raise TypeError(
                f"Not all elements of argument '{arg_name}' are of type "
                f"{list_check.underlying_type.__name__}"
            )

    return value


# -----------------------------------------------------------------------------
# Optional checks
# -----------------------------------------------------------------------------


def _is_optional(x: TypeAnnotation) -> bool:
    return (
        hasattr(x, "__origin__")
        and hasattr(x, "__args__")
        and getattr(x, "__origin__") is Union
        and len(getattr(x, "__args__", [])) == 2
        and _NoneType in getattr(x, "__args__")
    )


def _get_underlying_type_of_optional(x: TypeAnnotation) -> Optional[type]:
    # x.__args__ should be something like `(str, NoneType)` or `(typing.List[str], NoneType)`.
    # Note that an isinstance(t, type) check would only work in the plain `str` case.
    # Currently we're using an heuristic to cover the typing.XXX generics:
    for t in getattr(x, "__args__", []):
        if t != _NoneType and (isinstance(t, type) or _is_generic_type(t)):
            return cast(type, t)
    return None


class OptionalCheck(NamedTuple):
    underlying_type: Optional[type]

    @property
    def is_optional(self) -> bool:
        return self.underlying_type is not None


def check_for_optional(x: TypeAnnotation) -> OptionalCheck:
    if not _is_optional(x):
        return OptionalCheck(underlying_type=None)
    else:
        return OptionalCheck(underlying_type=_get_underlying_type_of_optional(x))


# -----------------------------------------------------------------------------
# List checks
# -----------------------------------------------------------------------------


def _is_list(x: TypeAnnotation) -> bool:
    if _is_optional(x):
        underlying_type_of_optional = _get_underlying_type_of_optional(x)
        if underlying_type_of_optional is not None:
            x = underlying_type_of_optional
    # In Python 3.6 __origin__ is List
    # In Python 3.7+ __origin__ is list
    origin = getattr(x, "__origin__", None)
    return (
        hasattr(x, "__origin__") and hasattr(x, "__args__") and (origin is List or origin is list)
    )


def _get_underlying_type_of_list(x: TypeAnnotation) -> type:
    if _is_optional(x):
        underlying_type_of_optional = _get_underlying_type_of_optional(x)
        if underlying_type_of_optional is not None:
            x = underlying_type_of_optional
    args = getattr(x, "__args__", [])
    if hasattr(x, "__args__") and len(args) >= 1:
        t = args[0]
        assert isinstance(t, type) or _is_generic_type(t), "Underlying type must be a type"
        # This cast may actually be invalid, because Optional and Union are not of type `type`.
        # and so a List[Optional[T]] would erroneously return an underlying type of type `type`.
        return cast(type, t)
    else:
        raise RuntimeError(f"Could not infer underlying type of {x}. Details:\n{_debug_repr(x)}")


class ListCheck(NamedTuple):
    underlying_type: Optional[type]

    @property
    def is_list(self) -> bool:
        return self.underlying_type is not None


def check_for_list(x: TypeAnnotation) -> ListCheck:
    if not _is_list(x):
        return ListCheck(underlying_type=None)
    else:
        return ListCheck(underlying_type=_get_underlying_type_of_list(x))
