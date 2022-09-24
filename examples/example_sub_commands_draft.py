#!/usr/bin/env python

import argparse
import sys
from typing import List, Union

from typed_argparse import App, SubParser, SubParsers, TypedArgs, WithUnionType, param
from typing_extensions import Literal


class CommonArgs(TypedArgs):
    verbose: bool = param(help="Enables verbose mode")


class ArgsFoo(CommonArgs):
    mode: Literal["foo"]
    file: str


class ArgsBar(CommonArgs):
    mode: Literal["bar"]
    src: str
    dst: str


Args = Union[ArgsFoo, ArgsBar]


def run_toplevel(args: CommonArgs) -> None:
    print(args)


def run_foo(args: ArgsFoo) -> None:
    print(args)


def run_bar(args: ArgsBar) -> None:
    print(args)


def main() -> None:
    App(run_toplevel, CommonArgs).run()

    App(
        SubParsers(
            SubParser("foo", run_foo, ArgsFoo, aliases=["co"]),
            SubParser("bar", run_bar, ArgsBar),
        ),
        CommonArgs,
    ).run()


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Verbose")
    subparsers = parser.add_subparsers(
        help="Available sub commands",
        dest="mode",
        required=True,
    )

    parser_foo = subparsers.add_parser("foo")
    parser_foo.add_argument("file", type=str)

    parser_bar = subparsers.add_parser("bar")
    parser_bar.add_argument("--src", required=True)
    parser_bar.add_argument("--dst", required=True)

    return WithUnionType[Args].validate(parser.parse_args(args))


if __name__ == "__main__":
    main()
