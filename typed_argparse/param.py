from typing import Any, NamedTuple, Optional, Sequence, TypeVar, overload


class Param(NamedTuple):
    flags: Sequence[str]
    required: bool
    positional: bool
    default: Optional[object]
    help: Optional[str]


T = TypeVar("T")


@overload
def param(
    *flags: str,
    required: bool = False,
    positional: bool = False,
    default: T,
    help: Optional[str] = None,
) -> T:
    ...


@overload
def param(
    *flags: str,
    required: bool = False,
    positional: bool = False,
    default: Optional[object] = None,
    help: Optional[str] = None,
) -> Any:
    ...


def param(
    *flags: str,
    required: bool = False,
    positional: bool = False,
    default: Optional[object] = None,
    help: Optional[str] = None,
) -> Any:
    return Param(
        flags=flags,
        required=required,
        positional=positional,
        default=default,
        help=help,
    )
