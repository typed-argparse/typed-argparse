from typing import (
    Any,
    Callable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Literal

NArgs = Union[Literal["*", "+"], int]


class Arg(NamedTuple):
    flags: Sequence[str]
    positional: bool
    default: Optional[object]
    type: Optional[Callable[[str], object]]
    nargs: Optional[NArgs]
    help: Optional[str]
    auto_default_help: bool


T = TypeVar("T")

# Overloads for default / type / default + type


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    default: T,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    type: Callable[[str], T],
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    default: T,
    type: Callable[[str], T],
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


# Overload for default / type / default + type with nargs


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    default: T,
    nargs: NArgs,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    type: Callable[[str], T],
    nargs: NArgs,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    default: T,
    type: Callable[[str], T],
    nargs: NArgs,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> T:
    ...


# Any fallback


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    nargs: NArgs,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> List[Any]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    nargs: Optional[NArgs] = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> Any:
    ...


# Impl


def arg(
    *flags: str,
    positional: bool = False,
    default: Optional[object] = None,
    type: Optional[Callable[[str], object]] = None,
    nargs: Optional[NArgs] = None,
    help: Optional[str] = None,
    auto_default_help: bool = True,
) -> Any:
    """
    Helper function to annotate arguments.

    The ``flags`` argument refers to the names of optional arguments in the CLI.
    Examples "-f", "--foo", "--some-optional-argument".

    All flags must start with an "-".

    Note: The name of positional arguments is taken from the variable name itself.
    There is no need to specify it separately.

    Available keyword arguments:
        - positional -- Whether to argument should be positional or an option.
        - default -- The default value of the argument.
        - type -- A type (= parser function) to convert from string to the target type.
        - nargs -- To specify the semantics of repeated arguments.
        - help -- The help text to show for the argument.
    """
    return Arg(
        flags=flags,
        positional=positional,
        default=default,
        type=type,
        nargs=nargs,
        help=help,
        auto_default_help=auto_default_help,
    )
