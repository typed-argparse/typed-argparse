#!/usr/bin/env python

import argparse
import sys

from typing import List, Union
from typing_extensions import Literal

from typed_argparse import TypedArgs, WithUnionType


class CommonArgs(TypedArgs):
    verbose: bool


class ArgsFoo(CommonArgs):
    mode: Literal["foo"]
    file: str


class ArgsBar(CommonArgs):
    mode: Literal["bar"]
    src: str
    dst: str


Args = Union[ArgsFoo, ArgsBar]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Verbose")
    subparsers = parser.add_subparsers(  # type: ignore
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


def main() -> None:
    args = parse_args()
    print(args)
    if args.mode == "foo":
        print(args.file)
    elif args.mode == "bar":
        print(args.src, args.dst)


if __name__ == "__main__":
    main()
