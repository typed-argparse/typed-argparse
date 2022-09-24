#!/usr/bin/env python


import argparse
import sys
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from .param import Param
from .type_utils import TypeAnnotation, collect_type_annotations
from .typed_argparse import TypedArgs

T = TypeVar("T")


class SubParser:
    def __init__(
        self,
        name: str,
        func: "FuncOrSubparsers[T]",
        typ: Type[T],
        aliases: Optional[List[str]] = None,
    ):
        self._name = name
        self._func = func
        self._typ = typ
        self._aliases = aliases


class SubParsers:
    def __init__(self, *subparsers: SubParser):
        self._subparsers = subparsers


FuncOrSubparsers = Union[Callable[[T], None], SubParsers]


class App:
    def __init__(self, func_or_subparsers: FuncOrSubparsers[T], typ: Optional[Type[T]] = None):
        self._func_or_subparsers = func_or_subparsers
        self._type = typ

    def run(self, raw_args: List[str] = sys.argv[1:]) -> None:
        parser = argparse.ArgumentParser()

        if not isinstance(self._func_or_subparsers, SubParsers):
            func = self._func_or_subparsers

            assert callable(func)
            assert self._type is not None
            assert issubclass(self._type, TypedArgs)

            _add_arguments(self._type, parser)

            parsed_args = parser.parse_args(raw_args)
            typed_args = self._type.from_argparse(parsed_args)

            func(typed_args)  # type: ignore

        else:
            subparser_decls = self._func_or_subparsers._subparsers

            if sys.version_info < (3, 7):
                subparsers = parser.add_subparsers(
                    help="Available sub commands",
                    dest="mode",
                )
            else:
                subparsers = parser.add_subparsers(
                    help="Available sub commands",
                    dest="mode",
                    required=True,
                )

            for subparser_decl in subparser_decls:
                sub_parser = subparsers.add_parser(subparser_decl._name)

                _add_arguments(subparser_decl._typ, sub_parser)  # type: ignore

            parsed_args = parser.parse_args(raw_args)
            # fmt: off
            # import IPython; IPython.embed()
            # fmt: on
            print(parsed_args)


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
