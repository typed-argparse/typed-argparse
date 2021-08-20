from typing import Any, Dict, List, NamedTuple, Optional, Union


_NoneType = type(None)


def _debug_repr(x: Any) -> Dict[str, Any]:
    return {name: getattr(x, name) for name in dir(x)}


def is_list(x: Any) -> bool:
    # In Python 3.6 __origin__ is List
    # In Python 3.7+ __origin__ is list
    return (
        hasattr(x, "__origin__")
        and hasattr(x, "__args__")
        and (x.__origin__ is List or x.__origin__ is list)
    )


def get_underlying_type_of_list(x: Any) -> type:
    if hasattr(x, "__args__") and len(x.__args__) >= 1:
        assert isinstance(x.__args__[0], type), "Underlying type must be a type"
        return x.__args__[0]
    else:
        raise RuntimeError(f"Could not infer underlying type of {x}. Details:\n{_debug_repr(x)}")


class ListCheck(NamedTuple):
    underlying_type: Optional[type]

    @property
    def is_list(self) -> bool:
        return self.underlying_type is not None


def check_for_list(x: Any) -> ListCheck:
    if not is_list(x):
        return ListCheck(underlying_type=None)
    else:
        return ListCheck(underlying_type=get_underlying_type_of_list(x))


def is_optional(x: Any) -> bool:
    return (
        hasattr(x, "__origin__")
        and hasattr(x, "__args__")
        and x.__origin__ is Union
        and len(x.__args__) == 2
    )


def get_underlying_type_of_optional(x: Any) -> Optional[type]:
    for t in x.__args__:
        if t != _NoneType and isinstance(t, type):
            return t
    return None


class OptionalCheck(NamedTuple):
    underlying_type: Optional[type]

    @property
    def is_optional(self) -> bool:
        return self.underlying_type is not None


def check_for_optional(x: Any) -> OptionalCheck:
    if not is_optional(x):
        return OptionalCheck(underlying_type=None)
    else:
        return OptionalCheck(underlying_type=get_underlying_type_of_optional(x))
