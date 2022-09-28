from typing import Any, Callable, NamedTuple, Optional, Sequence, TypeVar, overload


class Param(NamedTuple):
    flags: Sequence[str]
    required: bool
    positional: bool
    default: Optional[object]
    type: Optional[Callable[[str], object]]
    help: Optional[str]


T = TypeVar("T")


@overload
def param(
    *flags: str,
    required: bool = ...,
    positional: bool = ...,
    default: T,
    help: Optional[str] = ...,
) -> T:
    ...


@overload
def param(
    *flags: str,
    required: bool = ...,
    positional: bool = ...,
    type: Callable[[str], T],
    help: Optional[str] = ...,
) -> T:
    ...


@overload
def param(
    *flags: str,
    required: bool = ...,
    positional: bool = ...,
    default: T,
    type: Callable[[str], T],
    help: Optional[str] = ...,
) -> T:
    ...


@overload
def param(
    *flags: str,
    required: bool = ...,
    positional: bool = ...,
    help: Optional[str] = ...,
) -> Any:
    ...


def param(
    *flags: str,
    required: bool = False,
    positional: bool = False,
    default: Optional[object] = None,
    type: Optional[Callable[[str], object]] = None,
    help: Optional[str] = None,
) -> Any:
    return Param(
        flags=flags,
        required=required,
        positional=positional,
        default=default,
        type=type,
        help=help,
    )
