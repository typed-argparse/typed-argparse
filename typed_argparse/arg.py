import copy
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
    dynamic_default: Optional[Callable[[], object]]
    dynamic_choices: Optional[Callable[[], Sequence[object]]]
    type: Optional[Callable[[str], object]]
    nargs: Optional[NArgs]
    help: Optional[str]
    auto_default_help: bool

    def has_default(self) -> bool:
        has_default = self.default is not None
        has_dynamic_default = self.dynamic_default is not None
        return has_default or has_dynamic_default

    def nargs_with_default(self) -> NArgs:
        return self.nargs if self.nargs is not None else "*"

    def resolve_default(self) -> object:
        has_default = self.default is not None
        has_dynamic_default = self.dynamic_default is not None
        assert has_default or has_dynamic_default, "Argument has no default/dynamic_default."
        assert not (
            has_default and has_dynamic_default
        ), "default and dynamic_default are mutually exclusive. Please specify either."
        if has_default:
            # Note that argparse itself takes a copy of the default value, but not a deepcopy.
            return copy.deepcopy(self.default)
        else:
            assert self.dynamic_default is not None
            return self.dynamic_default()


T = TypeVar("T")


# Overloads for cases with only a single 'type revealing' field set


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: T,
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], T]],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    type: Callable[[str], T],
) -> T:
    ...


# Same for nargs


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: Sequence[T],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], Sequence[T]]],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


# Overloads for cases with two 'type revealing' field set


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: T,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], T]],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: T,
    type: Callable[[str], T],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], T]],
    type: Callable[[str], T],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
) -> T:
    ...


# Same for nargs


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: Sequence[T],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], Sequence[T]]],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: Sequence[T],
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


# Overloads for cases with three 'type revealing' field set


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: T,
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
) -> T:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], T]],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
) -> T:
    ...


# Same for nargs


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    default: Sequence[T],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    dynamic_default: Optional[Callable[[], Sequence[T]]],
    dynamic_choices: Optional[Callable[[], Sequence[T]]],
    type: Callable[[str], T],
    nargs: NArgs,
) -> List[T]:
    ...


# Any fallback


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
) -> Any:
    ...


@overload
def arg(
    *flags: str,
    positional: bool = ...,
    help: Optional[str] = ...,
    auto_default_help: bool = ...,
    nargs: NArgs,
) -> List[Any]:
    ...


# Impl


def arg(
    *flags: str,
    positional: bool = False,
    help: Optional[str] = None,
    auto_default_help: bool = True,
    nargs: Optional[NArgs] = None,
    default: Optional[object] = None,
    dynamic_default: Optional[Callable[[], object]] = None,
    dynamic_choices: Optional[Callable[[], Sequence[object]]] = None,
    type: Optional[Callable[[str], object]] = None,
) -> Any:
    """
    Helper function to annotate arguments.

    The ``flags`` argument refers to the names of optional arguments in the CLI.
    Examples "-f", "--foo", "--some-optional-argument".

    All flags must start with an "-".

    Note: The name of positional arguments is taken from the variable name itself.
    There is no need to specify it separately.

    Available keyword arguments:
        - positional -- Whether the argument should be positional or an option.
        - default -- The default value of the argument.
        - type -- A type (= parser function) to convert from string to the target type.
        - nargs -- To specify the semantics of repeated arguments.
        - help -- The help text to show for the argument.
    """
    return Arg(
        flags=flags,
        positional=positional,
        default=default,
        dynamic_default=dynamic_default,
        dynamic_choices=dynamic_choices,
        type=type,
        nargs=nargs,
        help=help,
        auto_default_help=auto_default_help,
    )
