from typing import Any, NamedTuple, Optional, TypeVar, overload


class Param(NamedTuple):
    required: bool
    positional: bool
    default: Optional[object]
    help: Optional[str]


T = TypeVar("T")


@overload
def param(
    *,
    required: bool = False,
    positional: bool = False,
    default: T,
    help: Optional[str] = None,
) -> T:
    ...


@overload
def param(
    *,
    required: bool = False,
    positional: bool = False,
    default: Optional[object] = None,
    help: Optional[str] = None,
) -> Any:
    ...


def param(
    *,
    required: bool = False,
    positional: bool = False,
    default: Optional[object] = None,
    help: Optional[str] = None,
) -> Any:
    return Param(
        required=required,
        positional=positional,
        default=default,
        help=help,
    )
