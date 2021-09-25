from collections.abc import Iterable
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union, cast


_NoneType = type(None)


# It looks like there is no good type annotation that works for "type annotations".
# `type` would work for internal types (int, str, ...) and some typing.XXX types
# like typing.List and typing.Dict, but it doesn't work for typing.Optional and
# typing.Union. For now, let's make no assumptions at all.
RawTypeAnnotation = object


def _get_origin(t: RawTypeAnnotation) -> Optional[object]:
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

    def validate(self, value: object) -> Tuple[object, Optional[str]]:

        underlying_if_optional = self.get_underlying_if_optional()
        if underlying_if_optional is not None:
            if value is None:
                return value, None
            else:
                return underlying_if_optional.validate(value)

        underlying_if_list = self.get_underlying_if_list()
        if underlying_if_list is not None:
            if value is None:
                # Coerce empty list.
                return [], None
            elif not isinstance(value, list):
                # allowing isinstance(value, Iterable) seems too lose, because it would allow
                # to coerce a list from string, which is not desirable.
                return value, f"value is not of type list, but {type(value).__name__}"
            else:
                new_values = []
                for x in value:
                    new_value, error = underlying_if_list.validate(x)
                    if error is not None:
                        return value, f"not all elements of the list have proper type ({error})"
                    new_values.append(new_value)
                return new_values, None

        # We have to assume self.raw_type is a true `type`
        assert isinstance(
            self.raw_type, type
        ), f"Type annotation is not of type 'type', but {type(self.raw_type).__name__}"
        if isinstance(value, self.raw_type):
            return value, None
        else:
            return (
                value,
                f"value is not of type {self.raw_type.__name__}, but {type(value).__name__}",
            )


def _debug_repr(x: Any) -> Dict[str, Any]:
    return {name: getattr(x, name) for name in dir(x)}


def _is_generic_type(x: RawTypeAnnotation) -> bool:
    # Heuristic to detect generic types. Consider using a type guard for an even cleaner
    # approach at the cost of adding typing_extensions as a dependency.
    return hasattr(x, "__origin__")


class TypeWrapper:
    def __init__(self, name: str, validate: Callable[[object], bool]) -> None:
        self.name = name
        self.validate = validate


def get_type_wrapper(x: RawTypeAnnotation) -> TypeWrapper:
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
    type_annotation: RawTypeAnnotation,
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


def _is_optional(x: RawTypeAnnotation) -> bool:
    return (
        hasattr(x, "__origin__")
        and hasattr(x, "__args__")
        and getattr(x, "__origin__") is Union
        and len(getattr(x, "__args__", [])) == 2
        and _NoneType in getattr(x, "__args__")
    )


def _get_underlying_type_of_optional(x: RawTypeAnnotation) -> Optional[type]:
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


def check_for_optional(x: RawTypeAnnotation) -> OptionalCheck:
    if not _is_optional(x):
        return OptionalCheck(underlying_type=None)
    else:
        return OptionalCheck(underlying_type=_get_underlying_type_of_optional(x))


# -----------------------------------------------------------------------------
# List checks
# -----------------------------------------------------------------------------


def _is_list(x: RawTypeAnnotation) -> bool:
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


def _get_underlying_type_of_list(x: RawTypeAnnotation) -> type:
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


def check_for_list(x: RawTypeAnnotation) -> ListCheck:
    if not _is_list(x):
        return ListCheck(underlying_type=None)
    else:
        return ListCheck(underlying_type=_get_underlying_type_of_list(x))
