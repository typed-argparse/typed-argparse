#!/usr/bin/env python

from typing import Union

from typed_argparse import Binding, Parser, SubParser, SubParserGroup, TypedArgs, arg


class CommonArgs(TypedArgs):
    verbose: bool = arg(help="Enables verbose mode")


class ArgsFoo(CommonArgs):
    file: str = arg(help="The file")


class ArgsBar(CommonArgs):
    src: str = arg(help="The source")
    dst: str = arg(help="The destination")


Args = Union[ArgsFoo, ArgsBar]


def run_toplevel(args: CommonArgs) -> None:
    print(args)


def run_foo(args: ArgsFoo) -> None:
    print(args)


def run_bar(args: ArgsBar) -> None:
    print(args)


def main() -> None:
    parser = Parser(
        SubParserGroup(
            SubParser("foo", ArgsFoo, aliases=["co"]),
            SubParser("bar", ArgsBar),
        ),
    )
    parser.run(
        lambda parser: parser.bind(
            Binding(CommonArgs, run_toplevel),
            Binding(ArgsFoo, run_foo),
            Binding(ArgsBar, run_bar),
        )
    )


if __name__ == "__main__":
    main()
