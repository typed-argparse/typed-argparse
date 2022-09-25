from typing import List, Type, TypeVar

from typed_argparse import Parser, TypedArgs, param

T = TypeVar("T", bound=TypedArgs)


def parse(arg_type: Type[T], raw_args: List[str]) -> T:
    args = Parser(arg_type).parse_args(raw_args)
    assert isinstance(args, arg_type)
    return args


def test_bool_switch() -> None:
    class Args(TypedArgs):
        verbose: bool = param(help="Enables verbose mode")

    args = parse(Args, [])
    assert args.verbose is False

    args = parse(Args, ["--verbose"])
    assert args.verbose is True


"""
def test_bool_switch__default_true() -> None:
    class Args(TypedArgs):
        verbose: bool = param("--no-verbose", default=True)

    args = parse(Args, [])
    assert args.verbose is True

    args = parse(Args, ["--no-verbose"])
    assert args.verbose is True
"""
