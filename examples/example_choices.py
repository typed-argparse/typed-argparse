#!/usr/bin/env python

import argparse
import sys
from typing import List
from typed_argparse import TypedArgs

from typing_extensions import Literal


class Args(TypedArgs):
    mode: Literal["a", "b", "c"]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=Args.get_choices_from("mode"),
    )
    return Args.from_argparse(parser.parse_args(args))


def main() -> None:
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
