#!/usr/bin/env python

from typing import Union

from typed_argparse import Binding, Parser, SubParser, SubParsers, TypedArgs, param


class CommonArgs(TypedArgs):
    verbose: bool = param(help="Enables verbose mode")


class ArgsFoo(CommonArgs):
    # mode: Literal["foo"]
    file: str = param(help="The file")


class ArgsBar(CommonArgs):
    # mode: Literal["bar"]
    src: str = param(help="The source")
    dst: str = param(help="The destination")


Args = Union[ArgsFoo, ArgsBar]


def run_toplevel(args: CommonArgs) -> None:
    print(args)


def run_foo(args: ArgsFoo) -> None:
    print(args)


def run_bar(args: ArgsBar) -> None:
    print(args)


def main() -> None:
    # Parser(CommonArgs).build_app(Binding(CommonArgs, run_toplevel)).run()

    Parser(
        SubParsers(
            SubParser("foo", ArgsFoo, aliases=["co"]),
            SubParser("bar", ArgsBar),
        )
    ).build_app(
        Binding(CommonArgs, run_toplevel),
        Binding(ArgsFoo, run_foo),
        Binding(ArgsBar, run_bar),
    ).run()

    """
    Parser(CommonArgs).build_app(
        Binding[CommonArgs](CommonArgs, run_toplevel),
        Binding[ArgsFoo](ArgsFoo, run_foo),
    ).run()
    """

    """
    App(
        SubParsers(
            SubParser("foo", run_foo, ArgsFoo, aliases=["co"]),
            SubParser("bar", run_bar, ArgsBar),
        ),
        CommonArgs,
    ).run()
    """


if __name__ == "__main__":
    main()
