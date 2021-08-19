import typing
from typing import Any, Dict


def _debug_repr(x: Any) -> Dict[str, Any]:
    return {name: getattr(x, name) for name in dir(x)}


def is_list(x: Any) -> bool:
    return hasattr(x, "__origin__") and (x.__origin__ is typing.List or x.__origin__ is list)


def get_underlying_type_of_list(x: Any) -> type:
    if hasattr(x, "__args__") and len(x.__args__) >= 1:
        assert isinstance(x.__args__[0], type), "Underlying type must be a type"
        return x.__args__[0]
    else:
        raise RuntimeError(f"Could not infer underlying type of {x}. Details:\n{_debug_repr(x)}")
