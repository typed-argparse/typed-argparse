#!/usr/bin/env python


import argparse
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .param import Param
from .type_utils import TypeAnnotation, collect_type_annotations
from .typed_argparse import TypedArgs


class SubParser:
    def __init__(
        self,
        name: str,
        func: "ArgsOrSubparsers",
        aliases: Optional[List[str]] = None,
    ):
        self._name = name
        self._func = func
        self._aliases = aliases


class SubParsers:
    def __init__(self, *subparsers: SubParser):
        self._subparsers = subparsers


ArgsOrSubparsers = Union[Type[TypedArgs], SubParsers]


# FuncMapping = Mapping[Type[TypedArgs], Callable[[TypedArgs], None]]
# FuncMappingElement = Tuple[Type[T], Callable[[T], None]]
# FuncMapping = Tuple[FuncMappingElement[T], ...]


"""
class Binding(NamedTuple, Generic[T]):
    arg_type: Type[T]
    func: Callable[[T], None]
"""


"""
class Binding(Generic[T]):
    def __init__(self, arg_type: Type[T], func: Callable[[T], None]):
        self.arg_type = arg_type
        self.func = func
"""

T = TypeVar("T", bound=TypedArgs)


class Binding:
    def __init__(self, arg_type: Type[T], func: Callable[[T], None]):
        self.arg_type: Type[TypedArgs] = arg_type
        self.func: Callable[[Any], None] = func


class Parser:
    def __init__(self, args_or_subparsers: ArgsOrSubparsers):
        self._args_or_subparsers = args_or_subparsers

    def parse_args(self, raw_args: List[str] = sys.argv[1:]) -> TypedArgs:
        parser = argparse.ArgumentParser()

        if not isinstance(self._args_or_subparsers, SubParsers):
            arg_type = self._args_or_subparsers
            assert issubclass(arg_type, TypedArgs)

            _add_arguments(arg_type, parser)

            parsed_args = parser.parse_args(raw_args)
            typed_args = arg_type.from_argparse(parsed_args)

            return typed_args

        else:
            subparser_decls = self._args_or_subparsers._subparsers

            if sys.version_info < (3, 7):
                subparsers = parser.add_subparsers(
                    help="Available sub commands",
                    # dest="mode1234",
                    title="mode",
                )
            else:
                subparsers = parser.add_subparsers(
                    help="Available sub commands",
                    # dest="mode1234",
                    title="mode",
                    # required=True,
                )

            for subparser_decl in subparser_decls:
                sub_parser = subparsers.add_parser(subparser_decl._name)

                _add_arguments(subparser_decl._typ, sub_parser)  # type: ignore

            parsed_args = parser.parse_args(raw_args)
            # fmt: off
            # import IPython; IPython.embed()
            # fmt: on
            print(parsed_args)

            raise RuntimeError("unimplemented")

    def build_app(self, *func_mapping: Binding) -> "App":
        # TODO: Validate, perhaps in App constructor to move invariant to class?
        return App(parser=self, func_mapping=func_mapping)


AnyParser = argparse.ArgumentParser


def _add_arguments(
    typ: Type[TypedArgs],
    parser: AnyParser,
) -> None:
    annotations = collect_type_annotations(typ, include_super_types=True)
    print(f"Annotations of {typ}: {annotations}")

    for attr_name, annotation in annotations.items():
        if not hasattr(typ, attr_name):
            raise RuntimeError(
                f"Type {typ} has no class attribute for '{attr_name}'. "
                "All parameters should have a '... = params(...)' declaration."
            )
        param = getattr(typ, attr_name)
        if not isinstance(param, Param):
            raise RuntimeError(
                f"Class attribute '{attr_name}' of type {typ} isn't of type Param. "
                "All parameters should have a '... = params(...)' declaration."
            )
        _add_argument(attr_name, annotation, param, parser)


def _add_argument(
    attr_name: str, annotation: TypeAnnotation, param: Param, parser: AnyParser
) -> None:
    name_or_flags = [f"--{attr_name}"]
    kwargs: Dict[str, Any] = {
        "help": param.help,
    }
    if annotation.is_bool:
        kwargs["action"] = "store_true"

    print(f"Adding argument: {name_or_flags} {kwargs}")
    parser.add_argument(*name_or_flags, **kwargs)


class App:
    def __init__(self, parser: Parser, func_mapping: Sequence[Binding]):
        self._parser = parser
        self._func_mapping = func_mapping

    def run(self, raw_args: List[str] = sys.argv[1:]) -> None:
        typed_args = self._parser.parse_args()

        for binding in self._func_mapping:
            if isinstance(typed_args, binding.arg_type):
                binding.func(typed_args)

        # Should be impossible due to correctness check
        raise AssertionError(
            f"Argument type {type(typed_args)} did not match anything in {self._func_mapping}."
        )
