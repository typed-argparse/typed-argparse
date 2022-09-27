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
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import assert_never

from .param import Param, param
from .type_utils import TypeAnnotation, collect_type_annotations
from .typed_argparse import TypedArgs

_ARG_COMPLETE_AVAILABLE = False

try:
    import argcomplete

    _ARG_COMPLETE_AVAILABLE = True
except ImportError:
    pass


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

        all_leaf_paths = _traverse_build_parser(self._args_or_subparsers, parser)
        type_mapping = _traverse_get_type_mapping(self._args_or_subparsers)

        if _ARG_COMPLETE_AVAILABLE:
            argcomplete.autocomplete(parser)

        argparse_namespace = parser.parse_args(raw_args)

        arg_type = _determine_arg_type(all_leaf_paths, argparse_namespace, type_mapping)

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


TypePath = Tuple[str, ...]


def _traverse_build_parser(
    args_or_subparsers: ArgsOrSubparsers,
    parser: ArgparseParser,
    cur_path: TypePath = (),
    all_leaf_paths: Optional[Set[TypePath]] = None,
) -> Set[TypePath]:
    if all_leaf_paths is None:
        all_leaf_paths = set()

    if isinstance(args_or_subparsers, SubParsers):
        subparser_decls = args_or_subparsers._subparsers

        # It looks like wrapping the `dest` variable for argparse into `<...>` leads to
        # well readable error message while also reducing the risk of an argument name
        # collision, because the argument gets appended to the argparse namespace in
        # its raw form. For instance: Namespace(file='f', verbose=False, **{'<sub-command>': 'foo'})
        dest = "<" + ((len(cur_path) + 1) * "sub-") + "command>"

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

            _traverse_build_parser(
                subparser_decl._args_or_subparsers,
                parser=sub_parser,
                cur_path=cur_path + (dest,),
                all_leaf_paths=all_leaf_paths,
            )

    elif issubclass(args_or_subparsers, TypedArgs):
        arg_type = args_or_subparsers
        assert issubclass(arg_type, TypedArgs)

        _add_arguments(arg_type, parser)

        all_leaf_paths.add(cur_path)

    else:
        assert_never(args_or_subparsers)

    return all_leaf_paths


TypeMapping = Dict[TypePath, Type[TypedArgs]]


def _traverse_get_type_mapping(args_or_subparsers: ArgsOrSubparsers) -> TypeMapping:

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


def _determine_arg_type(
    key_paths: Set[TypePath], argparse_namespace: argparse.Namespace, type_mapping: TypeMapping
) -> Type[TypedArgs]:
    # We sort leaf paths from longer (more specific) to shorter (less specific).
    # This should only become relevant when subparsers are non-mandatory, i.e.,
    # then can be executable with a shorter leaf path as well. In this case we
    # first have to check if a longer leaf path matches, otherwise it may be
    # possible that we accidentally execute the shorter leaf path logic.
    sorted_key_paths = sorted(
        key_paths,
        key=lambda leaf_path: len(leaf_path),
        reverse=True,
    )

    arg_type: Optional[Type[TypedArgs]] = None
    for key_path in sorted_key_paths:
        # Here we translate from the ('sub-command', 'sub-sub-command', ...) key-based path to the
        # actual value-based path of ('foo', 'x', ...) by lookup up the keys in the namespace.
        try:
            value_path: TypePath = tuple(getattr(argparse_namespace, dest) for dest in key_path)
            if value_path in type_mapping:
                arg_type = type_mapping[value_path]
                break
        except AttributeError:
            pass

    assert arg_type is not None, (
        f"Failed to extract argument type from namespace object {argparse_namespace} "
        f"(leaf paths: {sorted_key_paths}, type mapping: {type_mapping})"
    )
    return arg_type


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
