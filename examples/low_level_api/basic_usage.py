import argparse
import sys
from typing import List, Optional

from typed_argparse import TypedArgs


# Step 1: Add an argument type.
class Args(TypedArgs):
    foo: str
    num: Optional[int]
    files: List[str]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=str, required=True)
    parser.add_argument("--num", type=int)
    parser.add_argument("--files", type=str, nargs="*")
    # Step 2: Wrap the plain argparser result with your type.
    return Args.from_argparse(parser.parse_args(args))


def main() -> None:
    args = parse_args()
    # Step 3: Done, enjoy IDE auto-completion and strong type safety
    assert args.foo == "foo"
    assert args.num == 42
    assert args.files == ["a", "b", "c"]


if __name__ == "__main__":
    main()
