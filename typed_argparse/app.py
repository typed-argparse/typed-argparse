import argparse
import copy
import sys
from argparse import ArgumentParser as ArgparseParser
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import assert_never

from .param import Param, param
from .type_utils import TypeAnnotation, collect_type_annotations
from .typed_argparse import TypedArgs


class SubParser:
    def __init__(
        self,
        name: str,
        args_or_subparsers: "ArgsOrSubparsers",
        aliases: Optional[List[str]] = None,
    ):
        self._name = name
        self._args_or_subparsers = args_or_subparsers
        self._aliases = aliases


class SubParsers:
    def __init__(self, *subparsers: SubParser):
        self._subparsers = subparsers


ArgsOrSubparsers = Union[Type[TypedArgs], SubParsers]

T = TypeVar("T", bound=TypedArgs)


# Initially I considered making the bindings generic, but I don't think there is a significant
# benefit. It requires to write Binding[CommonArgs](CommonArgs, run_toplevel) on user site because
# the implicitly inferred generic arg seems to be Binding[TypedArg], which then leads to a type
# mismatch. Also, annotating the generics below in the usages felt awkward. This is probably a
# case where we want type erasure.
class Binding:
    def __init__(self, arg_type: Type[T], func: Callable[[T], None]):
        self.arg_type: Type[TypedArgs] = arg_type
        self.func: Callable[[Any], None] = func


class Parser:
    def __init__(self, args_or_subparsers: ArgsOrSubparsers):
        self._args_or_subparsers = args_or_subparsers

    def parse_args(self, raw_args: List[str] = sys.argv[1:]) -> TypedArgs:
        parser = argparse.ArgumentParser()

        dest_variables = _traverse_build_parser(self._args_or_subparsers, parser)
        type_mapping = _traverse_get_type_mapping(self._args_or_subparsers)

        argparse_namespace = parser.parse_args(raw_args)

        type_mapping_path = tuple(
            getattr(argparse_namespace, dest_variable) for dest_variable in dest_variables
        )
        arg_type = type_mapping[type_mapping_path]

        return arg_type.from_argparse(argparse_namespace)

    def build_app(self, *func_mapping: Binding) -> "App":
        # TODO: Validate, perhaps in App constructor to move invariant to class?
        return App(parser=self, func_mapping=func_mapping)


class App:
    def __init__(self, parser: Parser, func_mapping: Sequence[Binding]):
        self._parser = parser
        self._func_mapping = func_mapping

    def run(self, raw_args: List[str] = sys.argv[1:]) -> None:
        typed_args = self._parser.parse_args(raw_args)

        for binding in self._func_mapping:
            if isinstance(typed_args, binding.arg_type):
                binding.func(typed_args)
                return

        # Should be impossible due to correctness check
        raise AssertionError(
            f"Argument type {type(typed_args)} did not match anything in {self._func_mapping}."
        )


def _traverse_build_parser(
    args_or_subparsers: ArgsOrSubparsers,
    parser: ArgparseParser,
    dest_variables: Optional[List[str]] = None,
) -> List[str]:
    if dest_variables is None:
        dest_variables = []

    if isinstance(args_or_subparsers, SubParsers):
        subparser_decls = args_or_subparsers._subparsers

        dest = ((len(dest_variables) + 1) * "sub") + "command"
        dest_variables.append(dest)

        if sys.version_info < (3, 7):
            subparsers = parser.add_subparsers(
                help="Available sub commands",
                dest=dest,
            )
        else:
            subparsers = parser.add_subparsers(
                help="Available sub commands",
                dest=dest,
                required=True,
            )

        for subparser_decl in subparser_decls:
            sub_parser = subparsers.add_parser(subparser_decl._name)

            _traverse_build_parser(subparser_decl._args_or_subparsers, sub_parser, dest_variables)
            # _add_arguments(subparser_decl._typ, sub_parser)  # type: ignore

    elif issubclass(args_or_subparsers, TypedArgs):
        arg_type = args_or_subparsers
        assert issubclass(arg_type, TypedArgs)

        _add_arguments(arg_type, parser)

    else:
        assert_never(args_or_subparsers)

    return dest_variables


TypePath = Tuple[str, ...]


def _traverse_get_type_mapping(
    args_or_subparsers: ArgsOrSubparsers,
) -> Dict[TypePath, Type[TypedArgs]]:

    mapping: Dict[TypePath, Type[TypedArgs]] = {}

    def traverse(args_or_subparsers: ArgsOrSubparsers, current_path: TypePath) -> None:

        if isinstance(args_or_subparsers, SubParsers):
            subparser_decls = args_or_subparsers._subparsers
            for subparser_decl in subparser_decls:
                traverse(
                    args_or_subparsers=subparser_decl._args_or_subparsers,
                    current_path=current_path + (subparser_decl._name,),
                )

        elif issubclass(args_or_subparsers, TypedArgs):
            arg_type = args_or_subparsers
            mapping[current_path] = arg_type

        else:
            assert_never(args_or_subparsers)

    traverse(args_or_subparsers, current_path=tuple())

    return mapping


def _add_arguments(
    arg_type: Type[TypedArgs],
    parser: ArgparseParser,
) -> None:
    annotations = collect_type_annotations(arg_type, include_super_types=False)
    # print(f"Annotations of {arg_type}: {annotations}")

    for attr_name, annotation in annotations.items():
        if not hasattr(arg_type, attr_name):
            p = param()
        else:
            p = getattr(arg_type, attr_name)

        if not isinstance(p, Param):
            raise RuntimeError(
                f"Class attribute '{attr_name}' of type {type(p).__name__} isn't of type Param. "
                "All parameters should have a '... = params(...)' declaration."
            )

        args, kwargs = _build_add_argument_args(attr_name, annotation, p)

        # print(f"Adding argument: {args} {kwargs}")
        parser.add_argument(*args, **kwargs)


def _build_add_argument_args(
    attr_name: str,
    annotation: TypeAnnotation,
    p: Param,
) -> Tuple[List[str], Dict[str, Any]]:

    attr_name = attr_name.replace("_", "-")

    args: List[str] = []
    kwargs: Dict[str, Any] = {
        "help": p.help,
    }

    # TODO: Incorporate explicit naming
    is_positional = p.positional

    if annotation.is_bool:
        is_required = False
    else:
        if annotation.is_optional or p.default is not None or is_positional:
            is_required = False
        else:
            is_required = True

    # Note that argparse forbids setting 'required' at all for positional args,
    # so we must omit it if false.
    if is_required:
        kwargs["required"] = True

    if annotation.is_bool:
        if p.default is not None:
            if p.default is True:
                kwargs["action"] = "store_false"
            elif p.default is False:
                kwargs["action"] = "store_true"
            else:
                raise RuntimeError(f"Invalid default for bool '{p.default}'")
        else:
            kwargs["action"] = "store_true"

    else:
        # We must not declare 'type' for boolean switches, which have an action instead.
        type_converter = annotation.get_underlying_type_converter()
        if type_converter is not None:
            kwargs["type"] = type_converter

        if p.default is not None:
            kwargs["default"] = copy.deepcopy(p.default)

        allowed_values_if_literal = annotation.get_allowed_values_if_literal()
        if allowed_values_if_literal is not None:
            kwargs["choices"] = allowed_values_if_literal

        allowed_values_if_enum = annotation.get_allowed_values_if_enum()
        if allowed_values_if_enum is not None:
            kwargs["choices"] = allowed_values_if_enum

    if len(args) == 0:
        if p.positional:
            args += [f"{attr_name}"]
        else:
            args += [f"--{attr_name}"]

    return args, kwargs
