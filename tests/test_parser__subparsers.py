from typing import Union

import pytest
from typing_extensions import Literal

from typed_argparse import Binding, Parser, SubParser, SubParserGroup, TypedArgs, arg

from ._testing_utils import argparse_error


def test_subparser__basic() -> None:
    class FooArgs(TypedArgs):
        x: str

    class BarArgs(TypedArgs):
        y: str

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    args = parser.parse_args(["foo", "--x", "x_value"])
    assert isinstance(args, FooArgs)
    assert args.x == "x_value"

    args = parser.parse_args(["bar", "--y", "y_value"])
    assert isinstance(args, BarArgs)
    assert args.y == "y_value"


def test_subparser__multiple() -> None:
    class FooXA(TypedArgs):
        ...

    class FooXB(TypedArgs):
        ...

    class FooY(TypedArgs):
        ...

    class Bar(TypedArgs):
        ...

    parser = Parser(
        SubParserGroup(
            SubParser(
                "foo",
                SubParserGroup(
                    SubParser(
                        "x",
                        SubParserGroup(
                            SubParser("a", FooXA),
                            SubParser("b", FooXB),
                        ),
                    ),
                    SubParser("y", FooY),
                ),
            ),
            SubParser("bar", Bar),
        )
    )

    args = parser.parse_args(["foo", "x", "a"])
    assert isinstance(args, FooXA)
    args = parser.parse_args(["foo", "x", "b"])
    assert isinstance(args, FooXB)
    args = parser.parse_args(["foo", "y"])
    assert isinstance(args, FooY)
    args = parser.parse_args(["bar"])
    assert isinstance(args, Bar)


# Subparsers with common args


def test_subparsers_common_args__basic() -> None:
    class CommonArgs(TypedArgs):
        verbose: bool
        other: str = arg(default="default")

    class FooArgs(CommonArgs):
        x: str

    class BarArgs(CommonArgs):
        y: str

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
            common_args=CommonArgs,
        )
    )

    args = parser.parse_args(["foo", "--x", "x_value"])
    assert isinstance(args, FooArgs)
    assert args.x == "x_value"
    assert not args.verbose
    assert args.other == "default"

    args = parser.parse_args(["bar", "--y", "y_value"])
    assert isinstance(args, BarArgs)
    assert args.y == "y_value"
    assert not args.verbose
    assert args.other == "default"

    args = parser.parse_args(["--verbose", "--other", "1", "foo", "--x", "x_value"])
    assert isinstance(args, FooArgs)
    assert args.x == "x_value"
    assert args.verbose
    assert args.other == "1"

    args = parser.parse_args(["--verbose", "--other", "2", "bar", "--y", "y_value"])
    assert isinstance(args, BarArgs)
    assert args.y == "y_value"
    assert args.verbose
    assert args.other == "2"


def test_subparsers_common_args__via_inheritance_only() -> None:
    class CommonArgs(TypedArgs):
        verbose: bool
        other: str = arg(default="default")

    class FooArgs(CommonArgs):
        x: str

    class BarArgs(CommonArgs):
        y: str

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    args = parser.parse_args(["foo", "--x", "x_value"])
    assert isinstance(args, FooArgs)
    assert args.x == "x_value"
    assert not args.verbose

    args = parser.parse_args(["bar", "--y", "y_value"])
    assert isinstance(args, BarArgs)
    assert args.y == "y_value"
    assert not args.verbose

    args = parser.parse_args(["foo", "--x", "x_value", "--verbose", "--other", "1"])
    assert isinstance(args, FooArgs)
    assert args.x == "x_value"
    assert args.verbose
    assert args.other == "1"

    args = parser.parse_args(["bar", "--y", "y_value", "--verbose", "--other", "2"])
    assert isinstance(args, BarArgs)
    assert args.y == "y_value"
    assert args.verbose
    assert args.other == "2"


def test_subparsers_common_args__branch_isolation() -> None:
    class Root(TypedArgs):
        root: str = arg(default="root")

    class FooRoot(Root):
        foo_root: str = arg(default="foo_root")

    class FooA(FooRoot):
        a: str = arg(default="a")

    class FooB(FooRoot):
        b: str = arg(default="b")

    class Bar(Root):
        foo_root: str = arg(default="foo_root_in_other_branch")

    parser = Parser(
        SubParserGroup(
            SubParser(
                "foo",
                SubParserGroup(
                    SubParser("a", FooA),
                    SubParser("b", FooB),
                    common_args=FooRoot,
                ),
            ),
            SubParser("bar", Bar),
            common_args=Root,
        )
    )
    args = parser.parse_args(["foo", "a"])
    assert isinstance(args, FooA)
    assert args.root == "root"
    assert args.foo_root == "foo_root"
    assert args.a == "a"

    args = parser.parse_args(["bar"])
    assert isinstance(args, Bar)
    assert args.root == "root"
    assert args.foo_root == "foo_root_in_other_branch"


def test_subparsers_common_args__subparser_after_positional() -> None:
    class CommonArgs(TypedArgs):
        service: Literal["foo", "bar"] = arg(positional=True)

    class StartArgs(CommonArgs):
        ...

    class StopArgs(CommonArgs):
        ...

    parser = Parser(
        SubParserGroup(
            SubParser("start", StartArgs),
            SubParser("stop", StopArgs),
            common_args=CommonArgs,
        )
    )

    args = parser.parse_args(["foo", "start"])
    assert isinstance(args, StartArgs)
    assert args.service == "foo"

    args = parser.parse_args(["foo", "stop"])
    assert isinstance(args, StopArgs)
    assert args.service == "foo"

    args = parser.parse_args(["bar", "start"])
    assert isinstance(args, StartArgs)
    assert args.service == "bar"

    args = parser.parse_args(["bar", "stop"])
    assert isinstance(args, StopArgs)
    assert args.service == "bar"

    with argparse_error() as e:
        parser.parse_args(["start"])
    assert "argument service: invalid choice: 'start' (choose from 'foo', 'bar')" in str(e.error)

    with argparse_error() as e:
        parser.parse_args(["invalid", "start"])
    assert "argument service: invalid choice: 'invalid' (choose from 'foo', 'bar')" in str(e.error)


# Subparsers executable mapping behavior


def test_subparsers_executable_mapping_behavior() -> None:
    class CommonArgs(TypedArgs):
        ...

    class FooArgs(CommonArgs):
        ...

    class BarArgs(CommonArgs):
        ...

    num_run_common = 0
    num_run_foo = 0
    num_run_bar = 0

    def run_common(args: CommonArgs) -> None:
        nonlocal num_run_common
        num_run_common += 1

    def run_foo(args: FooArgs) -> None:
        nonlocal num_run_foo
        num_run_foo += 1

    def run_bar(args: BarArgs) -> None:
        nonlocal num_run_bar
        num_run_bar += 1

    # Required case

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
            common_args=CommonArgs,
        )
    )

    parser.bind(run_foo, run_bar).run(["foo"])
    assert (num_run_common, num_run_foo, num_run_bar) == (0, 1, 0)

    parser.bind(run_foo, run_bar).run(["bar"])
    assert (num_run_common, num_run_foo, num_run_bar) == (0, 1, 1)

    with pytest.raises(SystemExit):
        parser.bind(run_foo, run_bar).run([])

    # Non-required case

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
            common_args=CommonArgs,
            required=False,
        )
    )

    with pytest.raises(ValueError) as e:
        parser.bind(run_foo, run_bar).run([])
    assert "Incomplete bindings: There is no binding for type 'CommonArgs'." == str(e.value)

    with pytest.raises(ValueError) as e:
        parser.bind_lazy(lambda: [run_foo, run_bar]).run([])
    assert "Incomplete bindings: There is no binding for type 'CommonArgs'." == str(e.value)

    parser.bind(run_common, run_foo, run_bar).run([])
    assert (num_run_common, num_run_foo, num_run_bar) == (1, 1, 1)

    parser.bind(run_common, run_foo, run_bar).run(["foo"])
    assert (num_run_common, num_run_foo, num_run_bar) == (1, 2, 1)

    parser.bind(run_common, run_foo, run_bar).run(["bar"])
    assert (num_run_common, num_run_foo, num_run_bar) == (1, 2, 2)


# Bindings check


def test_bindings_check() -> None:
    class FooArgs(TypedArgs):
        x: str

    class BarArgs(TypedArgs):
        y: str

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    def foo(foo_args: FooArgs) -> None:
        ...

    def bar(bar_args: BarArgs) -> None:
        ...

    parser.bind(Binding(FooArgs, foo), Binding(BarArgs, bar))
    parser.bind(foo, bar)

    with pytest.raises(ValueError) as e:
        parser.bind(Binding(FooArgs, foo))
    assert "Incomplete bindings: There is no binding for type 'BarArgs'." == str(e.value)

    with pytest.raises(ValueError) as e:
        parser.bind(foo)
    assert "Incomplete bindings: There is no binding for type 'BarArgs'." == str(e.value)

    def func_with_no_args():  # type: ignore
        ...

    with pytest.raises(ValueError) as e:
        parser.bind(func_with_no_args)  # type: ignore
    assert "Type annotations of func_with_no_args are empty." == str(e.value)

    def func_with_no_annotations(x):  # type: ignore
        ...

    with pytest.raises(ValueError) as e:
        parser.bind(func_with_no_annotations)
    assert "Type annotations of func_with_no_annotations are empty." == str(e.value)

    def func_with_wrong_first_arg_1(x: int):  # type: ignore
        ...

    def func_with_wrong_first_arg_2(x: Union[str, int]):  # type: ignore
        ...

    with pytest.raises(ValueError) as e:
        parser.bind(func_with_wrong_first_arg_1)
    assert (
        "Expected first argument of func_with_wrong_first_arg_1 to be a "
        "subclass of 'TypedArgs' but got <class 'int'>."
    ) == str(e.value)

    with pytest.raises(ValueError) as e:
        parser.bind(func_with_wrong_first_arg_2)
    assert (
        "Expected first argument of func_with_wrong_first_arg_2 to be of type 'type' "
        "but got typing.Union[str, int]."
    ) == str(e.value)


# Misc


def test_readability_of_parser_structures() -> None:
    class FooArgs(TypedArgs):
        x: str

    class BarArgs(TypedArgs):
        y: str

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )
    expected = "Parser(SubParserGroup(SubParser('foo', FooArgs), SubParser('bar', BarArgs)))"
    assert str(parser) == expected
    assert repr(parser) == expected

    parser = Parser(FooArgs)
    expected = "Parser(FooArgs)"
    assert str(Parser(FooArgs)) == "Parser(FooArgs)"
    assert repr(Parser(FooArgs)) == "Parser(FooArgs)"