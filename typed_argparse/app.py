import argparse
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

from .param import Param
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

        type_mapping = _get_type_mapping(self._args_or_subparsers)

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


def _get_type_mapping(args_or_subparsers: ArgsOrSubparsers) -> Dict[TypePath, Type[TypedArgs]]:

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
    print(f"Annotations of {arg_type}: {annotations}")

    for attr_name, annotation in annotations.items():
        if not hasattr(arg_type, attr_name):
            raise RuntimeError(
                f"Type {arg_type} has no class attribute for '{attr_name}'. "
                "All parameters should have a '... = params(...)' declaration."
            )
        param = getattr(arg_type, attr_name)
        if not isinstance(param, Param):
            raise RuntimeError(
                f"Class attribute '{attr_name}' of type {arg_type} isn't of type Param. "
                "All parameters should have a '... = params(...)' declaration."
            )
        _add_argument(attr_name, annotation, param, parser)


def _add_argument(
    attr_name: str, annotation: TypeAnnotation, param: Param, parser: ArgparseParser
) -> None:
    name_or_flags = [f"--{attr_name}"]
    kwargs: Dict[str, Any] = {
        "help": param.help,
    }
    if not annotation.is_optional and not annotation.is_bool:
        kwargs["required"] = True
    if annotation.is_bool:
        kwargs["action"] = "store_true"

    print(f"Adding argument: {name_or_flags} {kwargs}")
    parser.add_argument(*name_or_flags, **kwargs)