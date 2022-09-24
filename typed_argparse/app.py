#!/usr/bin/env python

from __future__ import annotations

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
        func: FuncOrSubparsers[T],
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
    def __init__(self, func: FuncOrSubparsers[T], typ: Optional[Type[T]] = None):
        self._func = func
        self._type = typ

    def run(self, raw_args: List[str] = sys.argv[1:]) -> None:
        if callable(self._func):
            assert self._type is not None
            assert issubclass(self._type, TypedArgs)

            parser = argparse.ArgumentParser()

            build_argument_parser(self._type, parser)

            parsed_args = parser.parse_args(raw_args)
            typed_args = self._type.from_argparse(parsed_args)

            self._func(typed_args)  # type: ignore


# AnyParser = Union[argparse.ArgumentParser, argparse._SubParsersAction[argparse.ArgumentParser]]
AnyParser = argparse.ArgumentParser


def build_argument_parser(
    typ: Type[TypedArgs],
    parser: AnyParser,
) -> None:
    annotations = collect_type_annotations(typ)

    for field_name, annotation in annotations.items():
        param = getattr(typ, field_name)
        assert isinstance(param, Param)
        _add_argument(field_name, annotation, param, parser)


def _add_argument(
    field_name: str, annotation: TypeAnnotation, param: Param, parser: AnyParser
) -> None:
    name_or_flags = [f"--{field_name}"]
    kwargs: Dict[str, Any] = {
        "help": param.help,
    }
    if annotation.is_bool:
        kwargs["action"] = "store_true"

    parser.add_argument(*name_or_flags, **kwargs)
    # parser.add_argument(*name_or_flags, help=param.help)
    # fmt: off
    # import IPython; IPython.embed()
    # fmt: on
