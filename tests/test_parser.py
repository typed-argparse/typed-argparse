import argparse
import textwrap
from enum import Enum
from pathlib import Path
from typing import List, Optional, Type, TypeVar, Union

import pytest
from typing_extensions import Literal

from typed_argparse import Parser, TypedArgs, arg
from typed_argparse.parser import Bindings

from ._testing_utils import (
    argparse_error,
    compare_verbose,
    pre_python_3_10,
    remove_ansii_escape_sequences,
    starting_with_python_3_10,
)

T = TypeVar("T", bound=TypedArgs)


def parse(arg_type: Type[T], raw_args: List[str]) -> T:
    args = Parser(arg_type).parse_args(raw_args)
    assert isinstance(args, arg_type)
    return args


# Boolean


def test_bool_switch() -> None:
    class Args(TypedArgs):
        verbose: bool

    args = parse(Args, [])
    assert args.verbose is False

    args = parse(Args, ["--verbose"])
    assert args.verbose is True


def test_bool_switch__default_false() -> None:
    class Args(TypedArgs):
        verbose: bool = arg(default=False)

    args = parse(Args, [])
    assert args.verbose is False

    args = parse(Args, ["--verbose"])
    assert args.verbose is True


def test_bool_switch__default_true() -> None:
    class Args(TypedArgs):
        no_verbose: bool = arg(default=True)

    args = parse(Args, [])
    assert args.no_verbose is True

    args = parse(Args, ["--no-verbose"])
    assert args.no_verbose is False


def test_bool_switch__invalid_default() -> None:
    class Args(TypedArgs):
        verbose: bool = arg(default="foo")  # type: ignore

    with pytest.raises(RuntimeError) as e:
        parse(Args, [])

    assert str(e.value) == "Invalid default for bool 'foo'"


# Other scalar types


def test_other_scalar_types() -> None:
    class Args(TypedArgs):
        some_int: int
        some_float: float
        other_int: Optional[int]
        other_float: Optional[float]
        other_int_with_default: int = arg(default=43)
        other_float_with_default: float = arg(default=2.0)

    args = parse(Args, ["--some-int", "42", "--some-float", "1.0"])
    assert args.some_int == 42
    assert args.some_float == 1.0
    assert args.other_int is None
    assert args.other_float is None
    assert args.other_int_with_default == 43
    assert args.other_float_with_default == 2.0


def test_path() -> None:
    class Args(TypedArgs):
        path: Path

    args = parse(Args, ["--path", "/my/path"])
    assert args.path == Path("/my/path")


@starting_with_python_3_10
def test_variations_of_optionality() -> None:
    class Args(TypedArgs):
        traditional: Optional[int]
        as_union_a: Union[int, None]
        as_union_b: Union[None, int]
        as_union_modern_a: int | None  # type: ignore[syntax, unused-ignore]
        as_union_modern_b: None | int  # type: ignore[syntax, unused-ignore]

    args = parse(Args, [])
    assert args.traditional is None
    assert args.as_union_a is None
    assert args.as_union_b is None
    assert args.as_union_modern_a is None
    assert args.as_union_modern_b is None

    args = parse(
        Args,
        [
            "--traditional",
            "1",
            "--as-union-a",
            "2",
            "--as-union-b",
            "3",
            "--as-union-modern-a",
            "4",
            "--as-union-modern-b",
            "5",
        ],
    )
    assert args.traditional == 1
    assert args.as_union_a == 2
    assert args.as_union_b == 3
    assert args.as_union_modern_a == 4
    assert args.as_union_modern_b == 5


# Positional


def test_positional() -> None:
    class Args(TypedArgs):
        file: str = arg(positional=True)

    args = parse(Args, ["my_file"])
    assert args.file == "my_file"


def test_positional__with_default() -> None:
    class Args(TypedArgs):
        file_a: str = arg(positional=True, default="file_a")
        file_b: str = arg(positional=True, default="file_b")

    args = parse(Args, [])
    assert args.file_a == "file_a"
    assert args.file_b == "file_b"

    args = parse(Args, ["custom_a"])
    assert args.file_a == "custom_a"
    assert args.file_b == "file_b"

    args = parse(Args, ["custom_a", "custom_b"])
    assert args.file_a == "custom_a"
    assert args.file_b == "custom_b"


def test_positional__with_hyphens() -> None:
    """
    Since argparse does not allow positional arguments to have a `dest` that is different
    from the user-facing argument, we have an issue: By default we convert the
    positional_with_underscores to positional-with-underscores, because we want the user
    facing variable to have hyphens. Argparse will simply put it in the namespace under that
    spelling. In the validation in TypedArgs, we then look for a variable according to the
    name of the Python annotation, i.e., positional_with_underscores, and thus the lookup
    fails. As a work-around, we currently use a fallback lookup under the 'hyphened' name.
    """

    class Args(TypedArgs):
        positional_with_underscores: str = arg(positional=True)

    args = parse(Args, ["foo"])
    assert args.positional_with_underscores == "foo"


def test_positional__non_optional_list() -> None:
    class ArgsA(TypedArgs):
        single: str = arg(positional=True)
        multi: List[str] = arg(positional=True, nargs="+")

    args_a = parse(ArgsA, ["foo", "bar", "baz"])
    assert args_a.single == "foo"
    assert args_a.multi == ["bar", "baz"]

    class ArgsB(TypedArgs):
        multi: List[str] = arg(positional=True, nargs="+")
        single: str = arg(positional=True)

    args_b = parse(ArgsB, ["foo", "bar", "baz"])
    assert args_b.multi == ["foo", "bar"]
    assert args_b.single == "baz"


def test_positional__optional_list() -> None:
    class ArgsA(TypedArgs):
        single: str = arg(positional=True)
        multi: List[str] = arg(positional=True, nargs="*")

    args_a = parse(ArgsA, ["foo"])
    assert args_a.single == "foo"
    assert args_a.multi == []

    class ArgsB(TypedArgs):
        multi: List[str] = arg(positional=True, nargs="*")
        single: str = arg(positional=True)

    args_b = parse(ArgsB, ["foo"])
    assert args_b.multi == []
    assert args_b.single == "foo"


def test_positional__sandwiched() -> None:
    class Args(TypedArgs):
        single_before: str = arg(positional=True)
        multi: List[str] = arg(positional=True, nargs="*")
        single_after: str = arg(positional=True)

    args = parse(Args, ["foo", "baz"])
    assert args.single_before == "foo"
    assert args.multi == []
    assert args.single_after == "baz"

    args = parse(Args, ["foo", "bar", "baz"])
    assert args.single_before == "foo"
    assert args.multi == ["bar"]
    assert args.single_after == "baz"


def test_positional__optional_type() -> None:
    class Args(TypedArgs):
        value: Optional[int] = arg(positional=True)

    args = parse(Args, ["123"])
    assert args.value == 123

    args = parse(Args, [])
    assert args.value is None


def test_positional__optional_bool_not_allowed() -> None:
    class Args(TypedArgs):
        value: Optional[bool] = arg(positional=True)

    with pytest.raises(RuntimeError, match="Positional bool argument not supported"):
        parse(Args, [])


# Flags


def test_flags() -> None:
    class Args(TypedArgs):
        file: str = arg("-f")

    args = parse(Args, ["-f", "my_file"])
    assert args.file == "my_file"

    args = parse(Args, ["--file", "my_file"])
    assert args.file == "my_file"


def test_flags__renaming() -> None:
    class Args(TypedArgs):
        foo: str = arg("--bar")

    args = parse(Args, ["--bar", "bar"])
    assert args.foo == "bar"

    # TODO: Make this work with argparse_error
    with pytest.raises(SystemExit):
        parse(Args, ["--foo", "bar"])


def test_flags__single_char() -> None:
    class Args(TypedArgs):
        x: int = arg("-y")

    args = parse(Args, ["-y", "42"])
    assert args.x == 42

    # TODO: Make this work with argparse_error
    with pytest.raises(SystemExit):
        parse(Args, ["-x", "42"])


def test_flags__assert_no_positional_names() -> None:
    class Args(TypedArgs):
        foo: str = arg("foo")

    with pytest.raises(ValueError) as e:
        parse(Args, ["foo_value"])

    assert (
        "Invalid flags: ('foo',). All flags should start with '-'. "
        "A positional argument can be created by setting `positional=True`."
    ) == str(e.value)


# Type parser


def test_type_parsers() -> None:
    class ArgsIllegal1(TypedArgs):
        len_of_str: int = arg(type=lambda s: "")  # type: ignore

    class ArgsIllegal2(TypedArgs):
        foo: int = arg(default="", type=lambda s: len(s))  # type: ignore
        bar: str = arg(default="", type=lambda s: len(s))  # type: ignore

    class Args(TypedArgs):
        len_of_str: int = arg(positional=True, type=lambda s: len(s))

    assert parse(Args, ["1"]).len_of_str == 1
    assert parse(Args, ["12"]).len_of_str == 2
    assert parse(Args, ["123"]).len_of_str == 3


# Dynamic defaults


def test_dynamic_defaults() -> None:
    class Args(TypedArgs):
        foo: str = arg(dynamic_default=lambda: "foo_value")

    args = parse(Args, [])
    assert args.foo == "foo_value"


def test_dynamic_defaults__mutual_exclusiveness_check() -> None:
    class Args(TypedArgs):
        foo: str = arg(default="foo_value_1", dynamic_default=lambda: "foo_value_2")  # type: ignore

    with pytest.raises(AssertionError) as e:
        parse(Args, [])
    assert (
        str(e.value) == "default and dynamic_default are mutually exclusive. Please specify either."
    )


# Dynamic choices


def test_dynamic_choices() -> None:
    class Args(TypedArgs):
        foo: str = arg(dynamic_choices=lambda: ["a", "b"])

    args = parse(Args, ["--foo", "a"])
    assert args.foo == "a"
    args = parse(Args, ["--foo", "b"])
    assert args.foo == "b"

    with argparse_error() as e:
        parse(Args, ["--foo", "x"])
    assert "argument --foo: invalid choice: 'x' (choose from 'a', 'b')" == str(e.error)


# Literals


def test_literal__basics() -> None:
    class Args(TypedArgs):
        literal_string: Literal["a", "b"]
        literal_int: Literal[1, 2]

    args = parse(Args, ["--literal-string", "a", "--literal-int", "1"])
    assert args.literal_string == "a"
    assert args.literal_int == 1

    with argparse_error() as e:
        parse(Args, ["--literal-string", "c", "--literal-int", "1"])
    assert "argument --literal-string: invalid choice: 'c' (choose from 'a', 'b')" == str(e.error)

    with argparse_error() as e:
        parse(Args, ["--literal-string", "a", "--literal-int", "3"])
    assert "argument --literal-int: invalid choice: '3' (choose from 1, 2)" == str(e.error)


def test_literal__fuzzy_matching() -> None:
    class Args(TypedArgs):
        literal_string: Literal["some_foo", "SOME-BAR"]

    args = parse(Args, ["--literal-string", "some_foo"])
    assert args.literal_string == "some_foo"
    args = parse(Args, ["--literal-string", "some-foo"])
    assert args.literal_string == "some_foo"
    args = parse(Args, ["--literal-string", "SoMe-FoO"])
    assert args.literal_string == "some_foo"

    args = parse(Args, ["--literal-string", "some_bar"])
    assert args.literal_string == "SOME-BAR"
    args = parse(Args, ["--literal-string", "some-bar"])
    assert args.literal_string == "SOME-BAR"
    args = parse(Args, ["--literal-string", "SoMe-BaR"])
    assert args.literal_string == "SOME-BAR"

    with argparse_error():
        parse(Args, ["--literal-string", "some_foox"])
    with argparse_error():
        parse(Args, ["--literal-string", "xsome_foo"])
    with argparse_error():
        parse(Args, ["--literal-string", "somefoo"])


# Enums


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__basics(use_literal_enum: bool) -> None:
    if not use_literal_enum:

        class StrEnum(Enum):  # pyright: ignore
            a = "a-value"
            b = "b-value"

            def __repr__(self) -> str:
                return self.name

        class IntEnum(Enum):  # pyright: ignore
            a = 1
            b = 2

            def __repr__(self) -> str:
                return self.name

    else:

        class StrEnum(str, Enum):  # type: ignore
            a = "a-value"
            b = "b-value"

            def __repr__(self) -> str:
                return self.name

        class IntEnum(int, Enum):  # type: ignore
            a = 1
            b = 2

            def __repr__(self) -> str:
                return self.name

    class Args(TypedArgs):
        enum_string: StrEnum
        enum_int: IntEnum

    # Match by names
    args = parse(Args, ["--enum-string", "a", "--enum-int", "a"])
    assert args.enum_string == StrEnum.a
    assert args.enum_int == IntEnum.a

    # Match by values
    args = parse(Args, ["--enum-string", "a-value", "--enum-int", "1"])
    assert args.enum_string == StrEnum.a
    assert args.enum_int == IntEnum.a

    with argparse_error() as e:
        parse(Args, ["--enum-string", "c", "--enum-int", "a"])
    assert "argument --enum-string: invalid choice: 'c' (choose from a, b)" == str(e.error)  # noqa

    with argparse_error() as e:
        parse(Args, ["--enum-string", "a", "--enum-int", "c"])
    assert "argument --enum-int: invalid choice: 'c' (choose from a, b)" == str(e.error)


@pre_python_3_10
def test_enum__help_text(capsys: pytest.CaptureFixture[str]) -> None:
    class StrEnum(Enum):
        a = "a-value"
        b = "b-value"

        def __str__(self) -> str:
            return self.name

    class IntEnum(Enum):
        a = 1
        b = 2

        def __str__(self) -> str:
            return self.name

    class Args(TypedArgs):
        enum_string: StrEnum
        enum_int: IntEnum

    with pytest.raises(SystemExit):
        Parser(Args).parse_args(["-h"])

    captured = capsys.readouterr()
    assert captured.out == textwrap.dedent(
        """\
        usage: pytest [-h] --enum-string {a,b} --enum-int {a,b}

        optional arguments:
          -h, --help           show this help message and exit
          --enum-string {a,b}
          --enum-int {a,b}
        """
    )


@pytest.mark.parametrize("use_literal_enum", [False, True])
def test_enum__fuzzy_matching(use_literal_enum: bool) -> None:
    if not use_literal_enum:

        class StrEnum(Enum):  # pyright: ignore
            some_foo = "some_foo_value"
            SOME_BAR = "SOME-BAR_VALUE"

    else:

        class StrEnum(str, Enum):  # type: ignore
            some_foo = "some_foo_value"
            SOME_BAR = "SOME-BAR_VALUE"

    class Args(TypedArgs):
        enum_string: StrEnum

    args = parse(Args, ["--enum-string", "some_foo"])
    assert args.enum_string == StrEnum.some_foo
    args = parse(Args, ["--enum-string", "some-foo"])
    assert args.enum_string == StrEnum.some_foo
    args = parse(Args, ["--enum-string", "SoMe-FoO"])
    assert args.enum_string == StrEnum.some_foo

    args = parse(Args, ["--enum-string", "some_foo_value"])
    assert args.enum_string == StrEnum.some_foo
    args = parse(Args, ["--enum-string", "some-foo-value"])
    assert args.enum_string == StrEnum.some_foo
    args = parse(Args, ["--enum-string", "SoMe-FoO-VaLuE"])
    assert args.enum_string == StrEnum.some_foo

    args = parse(Args, ["--enum-string", "some_bar"])
    assert args.enum_string == StrEnum.SOME_BAR
    args = parse(Args, ["--enum-string", "some-bar"])
    assert args.enum_string == StrEnum.SOME_BAR
    args = parse(Args, ["--enum-string", "SoMe-BaR"])
    assert args.enum_string == StrEnum.SOME_BAR

    args = parse(Args, ["--enum-string", "some_bar_value"])
    assert args.enum_string == StrEnum.SOME_BAR
    args = parse(Args, ["--enum-string", "some-bar-value"])
    assert args.enum_string == StrEnum.SOME_BAR
    args = parse(Args, ["--enum-string", "SoMe-BaR-VaLuE"])
    assert args.enum_string == StrEnum.SOME_BAR

    with argparse_error():
        parse(Args, ["--enum-string", "some_foox"])
    with argparse_error():
        parse(Args, ["--enum-string", "xsome_foo"])
    with argparse_error():
        parse(Args, ["--enum-string", "somefoo"])


# Nargs


def test_nargs__basic_list_support() -> None:
    class Args(TypedArgs):
        files: List[Path]

    # TODO: Make this work with argparse_error
    with pytest.raises(SystemExit):
        args = parse(Args, [])

    args = parse(Args, ["--files"])
    assert args.files == []

    args = parse(Args, ["--files", "a", "b", "c"])
    assert args.files == [Path("a"), Path("b"), Path("c")]


def test_nargs__with_default__empty() -> None:
    class Args(TypedArgs):
        files: List[Path] = arg(default=[])

    args = parse(Args, [])
    assert args.files == []

    args = parse(Args, ["--files"])
    assert args.files == []


def test_nargs__with_default__non_empty() -> None:
    class Args(TypedArgs):
        actions: List[str] = arg(default=["foo", "bar"])

    args = parse(Args, [])
    assert args.actions == ["foo", "bar"]

    # Ensure copy semantics, i.e., that mutating the default doesn't mutate the instance we got.
    Args.actions.default.append("baz")  # type: ignore
    assert args.actions == ["foo", "bar"]

    args = parse(Args, ["--actions"])
    assert args.actions == []


def test_nargs__with_default__positional() -> None:
    class Args(TypedArgs):
        actions: List[str] = arg(positional=True, default=["foo", "bar"])

    args = parse(Args, [])
    assert args.actions == ["foo", "bar"]

    args = parse(Args, ["single"])
    assert args.actions == ["single"]


def test_nargs__with_explicit_nargs() -> None:
    class Args(TypedArgs):
        files: List[Path] = arg(nargs="*")

    args = parse(Args, ["--files"])
    assert args.files == []

    args = parse(Args, ["--files", "a", "b", "c"])
    assert args.files == [Path("a"), Path("b"), Path("c")]


def test_nargs__non_zero_nargs() -> None:
    class Args(TypedArgs):
        files: List[Path] = arg(nargs="+")

    with pytest.raises(SystemExit):
        parse(Args, ["--files"])

    args = parse(Args, ["--files", "a"])
    assert args.files == [Path("a")]


def test_nargs__fixed_number_of_args() -> None:
    class Args(TypedArgs):
        files: List[Path] = arg(nargs=2)

    with pytest.raises(SystemExit):
        parse(Args, ["--files", "a"])

    with pytest.raises(SystemExit):
        parse(Args, ["--files", "a", "b", "c"])

    args = parse(Args, ["--files", "a", "b"])
    assert args.files == [Path("a"), Path("b")]


def test_nargs__type_checks() -> None:
    class ArgsDefault(TypedArgs):
        files: List[str] = arg(nargs="*", default="foo")

    class ArgsType(TypedArgs):
        files: List[str] = arg(nargs="*", type=lambda s: s)

    class ArgsDefaultType(TypedArgs):
        files: List[str] = arg(nargs="*", type=lambda s: s, default="foo")

    class ArgsBadDefault(TypedArgs):
        files: List[str] = arg(nargs="*", default=42)  # type: ignore

    class ArgsBadType(TypedArgs):
        files: List[str] = arg(nargs="*", type=lambda s: 42)  # type: ignore

    class ArgsBadDefaultType(TypedArgs):
        files: List[str] = arg(nargs="*", type=lambda s: 42, default=42)  # type: ignore


# Nargs with optional


def test_nargs__list_wrapped_in_optional() -> None:
    class Args(TypedArgs):
        tags: Optional[List[str]]

    args = parse(Args, [])
    assert args.tags is None

    args = parse(Args, ["--tags"])
    assert args.tags == []

    args = parse(Args, ["--tags", "a", "b", "c"])
    assert args.tags == ["a", "b", "c"]


def test_nargs__list_wrapped_in_optional__illegal_with_nonzero_nargs() -> None:
    class Args(TypedArgs):
        tags: Optional[List[str]] = arg(nargs="+")

    with pytest.raises(AssertionError) as e:
        parse(Args, ["--tags", "a"])
    assert str(e.value) == "An argument with nargs='+' must not be optional"


# Nargs with choices


def test_nargs_with_choices__literal() -> None:
    Actions = Literal["a", "b"]

    class Args(TypedArgs):
        actions: List[Actions] = arg(positional=True, default=["a", "b"])  # pyright: ignore

    args = parse(Args, [])
    assert args.actions == ["a", "b"]
    args = parse(Args, ["a"])
    assert args.actions == ["a"]
    args = parse(Args, ["b"])
    assert args.actions == ["b"]
    args = parse(Args, ["a", "a", "b", "b", "a"])
    assert args.actions == ["a", "a", "b", "b", "a"]


def test_nargs_with_choices__literal_illegal_default() -> None:
    Actions = Literal["a", "b"]

    class Args(TypedArgs):
        actions: List[Actions] = arg(positional=True, default=["a", "b", "c"])  # type: ignore

    with argparse_error():
        parse(Args, [])


def test_nargs_with_choices__enum() -> None:
    class Actions(Enum):
        a = "a"
        b = "b"

    class Args(TypedArgs):
        actions: List[Actions] = arg(positional=True, default=[Actions.a, Actions.b])

    args = parse(Args, [])
    assert args.actions == [Actions.a, Actions.b]
    args = parse(Args, ["a"])
    assert args.actions == [Actions.a]
    args = parse(Args, ["b"])
    assert args.actions == [Actions.b]
    args = parse(Args, ["a", "a", "b", "b", "a"])
    assert args.actions == [Actions.a, Actions.a, Actions.b, Actions.b, Actions.a]


def test_nargs_with_choices__enum_illegal_default() -> None:
    class Actions(Enum):
        a = "a"
        b = "b"

    class Args(TypedArgs):
        actions: List[Actions] = arg(
            positional=True,
            default=[Actions.a, Actions.b, "c"],  # type: ignore
        )

    with argparse_error():
        parse(Args, [])


def test_nargs_with_choices__dynamic_choices_and_dynamic_default() -> None:
    class Args(TypedArgs):
        actions: List[str] = arg(
            positional=True,
            nargs="*",
            dynamic_default=lambda: ["a", "b"],
            dynamic_choices=lambda: ["a", "b"],
        )

    args = parse(Args, [])
    assert args.actions == ["a", "b"]
    args = parse(Args, ["a"])
    assert args.actions == ["a"]
    args = parse(Args, ["b"])
    assert args.actions == ["b"]
    args = parse(Args, ["a", "a", "b", "b", "a"])
    assert args.actions == ["a", "a", "b", "b", "a"]


# Run


def test_parser_run() -> None:
    class Args(TypedArgs):
        verbose: bool

    was_executed = False

    def runner(args: Args) -> None:
        nonlocal was_executed
        was_executed = True
        assert args.verbose

    Parser(Args).bind(runner).run(["--verbose"])

    assert was_executed


def test_parser_run__typical_lazy_syntax() -> None:
    class Args(TypedArgs):
        verbose: bool

    was_executed = False

    def runner(args: Args) -> None:
        nonlocal was_executed
        was_executed = True
        assert args.verbose

    def make_bindings() -> Bindings:
        return [runner]

    Parser(Args).bind_lazy(make_bindings).run(["--verbose"])

    assert was_executed


# Defaults in help text


@pre_python_3_10
def test_defaults_in_help_text__on_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        epsilon: float = arg(help="Some epsilon", default=0.1)

    parser = Parser(Args)
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])

    captured_help = remove_ansii_escape_sequences(capsys.readouterr().out)
    assert captured_help == textwrap.dedent(
        """\
        usage: pytest [-h] [--epsilon EPSILON]

        optional arguments:
          -h, --help         show this help message and exit
          --epsilon EPSILON  Some epsilon [default: 0.1]
        """
    )


@pre_python_3_10
def test_defaults_in_help_text__off_if_desired(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        epsilon: float = arg(help="Some epsilon", default=0.1, auto_default_help=False)

    parser = Parser(Args)
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])

    captured = remove_ansii_escape_sequences(capsys.readouterr().out)
    assert captured == textwrap.dedent(
        """\
        usage: pytest [-h] [--epsilon EPSILON]

        optional arguments:
          -h, --help         show this help message and exit
          --epsilon EPSILON  Some epsilon
        """
    )


# Support of formatter class in help texts


@pre_python_3_10
def test_formatter_class_support(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        foo: int = arg(help="arg line1\narg line2")

    parser = Parser(
        Args,
        description="description line 1\ndescription line 2\ndescription line 3",
        epilog="epilog line 1\nepilog line 2\nepilog line 3",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])

    captured = remove_ansii_escape_sequences(capsys.readouterr().out)
    compare_verbose(
        captured,
        textwrap.dedent(
            """\
            usage: pytest [-h] --foo FOO

            description line 1
            description line 2
            description line 3

            optional arguments:
              -h, --help  show this help message and exit
              --foo FOO   arg line1
                          arg line2

            epilog line 1
            epilog line 2
            epilog line 3
            """
        ),
    )


# Custom names for meta vars


@pre_python_3_10
def test_metavars_in_help_text(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        epsilon: float = arg(help="Some epsilon", metavar="E", default=0.1)

    parser = Parser(Args)
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])

    captured_help = remove_ansii_escape_sequences(capsys.readouterr().out)
    assert captured_help == textwrap.dedent(
        """\
        usage: pytest [-h] [--epsilon E]

        optional arguments:
          -h, --help   show this help message and exit
          --epsilon E  Some epsilon [default: 0.1]
        """
    )


@pre_python_3_10
def test_metavars_in_help_text_not_allowed_for_bool(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        epsilon: bool = arg(metavar="X")

    with pytest.raises(RuntimeError, match="Cannot set metavar for boolean argument"):
        Parser(Args)


# Misc


@pre_python_3_10
def test_forwarding_of_argparse_kwargs(capsys: pytest.CaptureFixture[str]) -> None:
    class Args(TypedArgs):
        verbose: bool

    parser = Parser(
        Args,
        prog="my_prog",
        usage="my_usage",
        description="my description",
        epilog="my epilog",
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])

    captured = remove_ansii_escape_sequences(capsys.readouterr().out)
    assert captured == textwrap.dedent(
        """\
        usage: my_usage

        my description

        optional arguments:
          -h, --help  show this help message and exit
          --verbose

        my epilog
        """
    )


def test_illegal_param_type() -> None:
    class Args(TypedArgs):
        foo: str = "default"

    with pytest.raises(RuntimeError) as e:
        Parser(Args).parse_args([])

    assert "Class attribute 'foo' of type str isn't of type Arg." in str(e.value)
