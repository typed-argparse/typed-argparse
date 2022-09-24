#!/usr/bin/env python

import argparse
import sys
from typing import List, Optional
from typed_argparse import TypedArgs


class Args(TypedArgs):
    foo: str
    num: Optional[int]
    files: List[str]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=str, required=True)
    parser.add_argument("--num", type=int)
    parser.add_argument("--files", type=str, nargs="*")
    return Args.from_argparse(parser.parse_args(args))


def main() -> None:
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
