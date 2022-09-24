import argparse
import sys
from typing import List, Optional

from typed_argparse import TypedArgs


def test_example_basic() -> None:
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

    args = parse_args(["--foo", "foo"])
    assert args.foo == "foo"
    assert args.num is None
    assert args.files == []

    args = parse_args(["--foo", "foo", "--num", "42", "--files", "a", "b", "c"])
    assert args.foo == "foo"
    assert args.num == 42
    assert args.files == ["a", "b", "c"]
