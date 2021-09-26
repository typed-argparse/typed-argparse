#!/usr/bin/env python

import argparse
import sys
from typing import List
from typed_argparse import TypedArgs, get_choices_from

from typing_extensions import Literal


class MyArgs(TypedArgs):
    mode: Literal["a", "b", "c"]


def parse_args(args: List[str] = sys.argv[1:]) -> MyArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=get_choices_from(MyArgs, "mode"),
    )
    return MyArgs(parser.parse_args(args))


def main() -> None:
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
