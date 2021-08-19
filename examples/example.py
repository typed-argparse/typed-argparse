#!/usr/bin/env python

import argparse
import sys
from typing import List
from typed_argparse import TypedArgs


class MyArgs(TypedArgs):
    foo: str
    num: int
    # files: List[str]


def parse_args(args: List[str] = sys.argv[1:]) -> MyArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=str)
    parser.add_argument("--num", type=int)
    # parser.add_argument("--files", type=str, nargs="*")
    return MyArgs(parser.parse_args(args))


def main() -> None:
    args = parse_args(["--foo", "foo", "--num", "42", "--files", "a", "b", "c"])
    assert args.foo == "foo"
    assert args.num == 42
    # assert args.files == ["a", "b", "c"]


if __name__ == "__main__":
    main()
