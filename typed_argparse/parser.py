from __future__ import annotations

import argparse
import sys
from argparse import ArgumentParser as ArgparseParser
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

from typing_extensions import assert_never

from ._argparse_abstractions import (
    AddParserKwArgs,
    FormatterClass,
    create_argparse_parser,
)
from .arg import Arg
from .arg import arg as make_arg
from .choices import Choices
from .exceptions import SubParserConflict
from .formatter import DefaultHelpFormatter
from .type_utils import TypeAnnotation, collect_type_annotations
from .typed_args import TypedArgs

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

    @staticmethod
    def from_func(func: Callable[[Any], None]) -> Binding:
        if not hasattr(func, "__annotations__"):
            raise ValueError(f"Function {func.__name__} misses type annotations.")

        annotations = get_type_hints(func)

        if len(annotations) == 0:
            raise ValueError(f"Type annotations of {func.__name__} are empty.")

        first_type: object = next(iter(annotations.values()))

        if not isinstance(first_type, type):
            raise ValueError(
                f"Expected first argument of {func.__name__} to be of type 'type' "
                f"but got {first_type}."
            )
        else:
            if not issubclass(first_type, TypedArgs):
                raise ValueError(
                    f"Expected first argument of {func.__name__} to be a subclass of 'TypedArgs' "
                    f"but got {first_type}."
                )
            else:
                return Binding(first_type, func)


def _homogenize_bindings(bindings: "Bindings") -> List[Binding]:
    return [
        binding if isinstance(binding, Binding) else Binding.from_func(binding)
        for binding in bindings
    ]


class SubParser:
    def __init__(
        self,
        name: str,
        args_or_group: ArgsOrGroup,
        help: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ):
        self._name = name
        self._args_or_group = args_or_group
        self._aliases = aliases
        self._help = help

    def __str__(self) -> str:
        return f"SubParser('{self._name}', {_to_string(self._args_or_group)})"

    def __repr__(self) -> str:
        return str(self)


class SubParserGroup:
    def __init__(
        self,
        *subparsers: SubParser,
        common_args: Optional[Type[TypedArgs]] = None,
        description: Optional[str] = None,
        required: bool = True,
    ):
        self._sub_parser_declarations = subparsers
        self._common_args = common_args
        self._required = required
        self._description = description

    def __str__(self) -> str:
        return f"SubParserGroup({', '.join(map(str, self._sub_parser_declarations))})"

    def __repr__(self) -> str:
        return str(self)


class Parser:
    """
    This class offers a declarative API to wrap argparse based on TypedArgs definitions.
    """

    def __init__(
        self,
        args_or_group: ArgsOrGroup,
        prog: Optional[str] = None,
        usage: Optional[str] = None,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        add_help: bool = True,
        allow_abbrev: bool = True,
        formatter_class: Optional[FormatterClass] = DefaultHelpFormatter,
    ):
        """
        The parser constructor requires one positional argument, which is either
        - directly a TypedArgs type to be used to define the arguments
        - a SubParserGroup, which itself contains TypedArgs within subparsers.

        Keyword arguments forwarded to argparse:
            - prog -- The name of the program (default: sys.argv[0])
            - usage -- A usage message (default: auto-generated from arguments)
            - description -- A description of what the program does
            - epilog -- Text following the argument descriptions
            - add_help -- Add a -h/-help option
            - allow_abbrev -- Allow long options to be abbreviated unambiguously
            - formatter_class -- A argparse conforming formatter class
        """

        self._args_or_group = args_or_group

        # Build type mapping including validation of subparser structure. Note that older versions
        # of argparse do not internally detect conflicting subparsers, while newer versions do. In
        # order to obtain consistent behavior we pre-validate the subparser structure before
        # constructing the actual argparse subparser. This ensures consistently throwing the same
        # SubParserConflict across all Python versions.
        self._type_mapping = _traverse_get_type_mapping(self._args_or_group)

        # Build the argparse parser.
        self._argparse_parser = create_argparse_parser(
            prog=prog,
            usage=usage,
            description=description,
            epilog=epilog,
            add_help=add_help,
            allow_abbrev=allow_abbrev,
            formatter_class=formatter_class,
        )
        self._all_leaf_dest_paths = _traverse_build_parser(
            self._args_or_group, self._argparse_parser
        )

    def parse_args(self, raw_args: List[str] = sys.argv[1:]) -> TypedArgs:
        """
        Parses the given list of arguments into a TypedArgs instance.
        """

        _install_argcomplete_if_available(self._argparse_parser)

        argparse_namespace = self._argparse_parser.parse_args(raw_args)

        # print("Raw args:", raw_args)
        # print("Argparse namespace:", argparse_namespace)

        arg_type = _determine_arg_type(
            self._all_leaf_dest_paths, argparse_namespace, self._type_mapping
        )

        if arg_type is None:
            # Edge case to investigate: Probably only possible if subparsers are set to
            # non-required, and none matched.
            self._argparse_parser.exit(
                message=f"Failed to extract argument type from namespace object: "
                f"{argparse_namespace}\n"
                f"dest paths: {self._all_leaf_dest_paths}\n"
                f"type mapping: {self._type_mapping}"
            )

        else:
            return arg_type.from_argparse(argparse_namespace)

    def verify(self, bindings: "Bindings") -> None:
        """
        Verifies the completeness of a given list of bindings w.r.t. this parser structure.

        Raises a ValueError is the bindings are complete.
        """
        offered_bindings = set(binding.arg_type for binding in _homogenize_bindings(bindings))

        for arg_type in self._type_mapping.values():
            if arg_type not in offered_bindings:
                raise ValueError(
                    f"Incomplete bindings: There is no binding for type '{arg_type.__name__}'."
                )

    def bind(self, *binding: AnyBinding) -> "App":
        """
        Turn the parser into an executable app (with eager bindings).

        Bindings are verified immediately.
        """
        bindings = list(binding)
        self.verify(bindings)
        return App(self, bindings)

    def bind_lazy(self, lazy_bindings: LazyBindings) -> "App":
        """
        Turn the parser into an executable app (with lazy bindings).

        Bindings verification is postponed into running the app.
        """
        return App(self, lazy_bindings)

    def __str__(self) -> str:
        return f"Parser({_to_string(self._args_or_group)})"

    def __repr__(self) -> str:
        return str(self)


class App:
    def __init__(self, parser: Parser, bindings: EagerOrLazyBindings):
        self._parser = parser
        self._bindings = bindings

    def run(self, raw_args: List[str] = sys.argv[1:]) -> None:
        """
        Parse arguments, verify the (possibly lazy) bindings, and execute them.
        """

        # Argument parsing must come first for responsiveness
        typed_args = self._parser.parse_args(raw_args)

        # Resolve possibly lazy bindings
        if callable(self._bindings):
            bindings = self._bindings()
        else:
            bindings = self._bindings

        # Verify bindings
        self._parser.verify(bindings)

        # Identify bindings branch to execute
        for binding in _homogenize_bindings(bindings):
            # Note that we don't want `isinstance` but rather exact type equality here,
            # so that we don't accidentally execute a base function.
            if type(typed_args) is binding.arg_type:
                binding.func(typed_args)
                return

        # Should be impossible due to correctness check
        raise AssertionError(
            f"Argument type {type(typed_args)} did not match anything in {bindings}."
        )


ArgsOrGroup = Union[Type[TypedArgs], SubParserGroup]

AnyBinding = Union[Binding, Callable[[Any], None]]
Bindings = List[AnyBinding]
LazyBindings = Callable[[], Bindings]
EagerOrLazyBindings = Union[Bindings, LazyBindings]


DestPath = Tuple[str, ...]


def _traverse_build_parser(
    args_or_group: ArgsOrGroup,
    parser: ArgparseParser,
    cur_dest_path: DestPath = (),
    parent_annotations: Optional[Set[str]] = None,
    all_leaf_dest_paths: Optional[Set[DestPath]] = None,
) -> Set[DestPath]:
    if parent_annotations is None:
        parent_annotations = set()
    if all_leaf_dest_paths is None:
        all_leaf_dest_paths = set()

    if isinstance(args_or_group, SubParserGroup):
        group = args_or_group

        # Make a copy of parent annotations to avoid leaking changes in other branches.
        parent_annotations = parent_annotations.copy()

        if group._common_args is not None:
            common_args = group._common_args
            _add_arguments(common_args, parser, parent_annotations)

            if not args_or_group._required:
                all_leaf_dest_paths.add(cur_dest_path)

            parent_annotations.update(collect_type_annotations(common_args).keys())

        # It looks like wrapping the `dest` variable for argparse into `<...>` leads to
        # well readable error message while also reducing the risk of an argument name
        # collision, because the argument gets appended to the argparse namespace in
        # its raw form. For instance: Namespace(file='f', verbose=False, **{'<sub-command>': 'foo'})
        # Note that this later requires to use `getattr(argparse_namespace, dest)` to pull
        # the corresponding values out of the argparse namespace.
        dest = "<" + ((len(cur_dest_path) + 1) * "sub-") + "command>"

        argparse_subparsers = parser.add_subparsers(
            help="Available sub commands",
            dest=dest,
            description=group._description,
            required=group._required,
        )

        for sub_parser_declaration in group._sub_parser_declarations:
            kwargs: AddParserKwArgs = {}
            if sub_parser_declaration._help is not None:
                kwargs["help"] = sub_parser_declaration._help
            if sub_parser_declaration._aliases is not None:
                kwargs["aliases"] = sub_parser_declaration._aliases
            argparse_subparser = argparse_subparsers.add_parser(
                sub_parser_declaration._name, **kwargs
            )

            _traverse_build_parser(
                sub_parser_declaration._args_or_group,
                parser=argparse_subparser,
                cur_dest_path=cur_dest_path + (dest,),
                parent_annotations=parent_annotations,
                all_leaf_dest_paths=all_leaf_dest_paths,
            )

    elif issubclass(args_or_group, TypedArgs):
        arg_type = args_or_group
        assert issubclass(arg_type, TypedArgs)

        _add_arguments(arg_type, parser, parent_annotations)

        all_leaf_dest_paths.add(cur_dest_path)

    else:
        assert_never(args_or_group)

    return all_leaf_dest_paths


TypeMapping = Dict[DestPath, Type[TypedArgs]]


def _traverse_get_type_mapping(args_or_group: ArgsOrGroup) -> TypeMapping:

    mapping: Dict[DestPath, Type[TypedArgs]] = {}

    def traverse(args_or_group: ArgsOrGroup, current_path: DestPath) -> None:

        if isinstance(args_or_group, SubParserGroup):
            group = args_or_group

            if group._common_args is not None and not group._required:
                mapping[current_path] = group._common_args

            subparser_decls = group._sub_parser_declarations
            for subparser_decl in subparser_decls:
                traverse(
                    args_or_group=subparser_decl._args_or_group,
                    current_path=current_path + (subparser_decl._name,),
                )
                # If the subparser has aliases, we also need to register them in the type mapping.
                if subparser_decl._aliases is not None:
                    for alias in subparser_decl._aliases:
                        traverse(
                            args_or_group=subparser_decl._args_or_group,
                            current_path=current_path + (alias,),
                        )

        elif issubclass(args_or_group, TypedArgs):
            arg_type = args_or_group
            if current_path in mapping:
                raise SubParserConflict(
                    f"Detected a sub parser conflict: Adding sub parser `{arg_type.__qualname__}` at sub "
                    f"parser path {current_path} conflicts with other sub parser "
                    f"`{mapping[current_path].__qualname__}`."
                )
            else:
                mapping[current_path] = arg_type

        else:
            assert_never(args_or_group)

    traverse(args_or_group, current_path=tuple())

    return mapping


def _determine_arg_type(
    all_leaf_dest_paths: Set[DestPath],
    argparse_namespace: argparse.Namespace,
    type_mapping: TypeMapping,
) -> Optional[Type[TypedArgs]]:
    # We sort leaf paths from longer (more specific) to shorter (less specific).
    # This should only become relevant when subparsers are non-mandatory, i.e.,
    # then can be executable with a shorter leaf path as well. In this case we
    # first have to check if a longer leaf path matches, otherwise it may be
    # possible that we accidentally execute the shorter leaf path logic.
    sorted_dest_paths = sorted(
        all_leaf_dest_paths,
        key=lambda leaf_path: len(leaf_path),
        reverse=True,
    )

    arg_type: Optional[Type[TypedArgs]] = None
    for dest_path in sorted_dest_paths:
        # Here we translate from the ('sub-command', 'sub-sub-command', ...) key-based dest path to the
        # actual value-based path of ('foo', 'x', ...) by looking up the keys in the namespace.
        try:
            value_path: Tuple[str, ...] = tuple(
                getattr(argparse_namespace, dest) for dest in dest_path
            )
            if value_path in type_mapping:
                arg_type = type_mapping[value_path]
                return arg_type
        except AttributeError:
            pass

    return None


def _add_arguments(
    arg_type: Type[TypedArgs], parser: ArgparseParser, parent_annotations: Set[str]
) -> None:
    annotations = collect_type_annotations(arg_type)
    # print(f"Adding {arg_type.__name__}, {annotations.keys() = }, {parent_annotations = }")

    for attr_name, annotation in annotations.items():
        if attr_name in parent_annotations:
            continue

        if not hasattr(arg_type, attr_name):
            arg = make_arg()
        else:
            arg = getattr(arg_type, attr_name)

        if not isinstance(arg, Arg):
            raise RuntimeError(
                f"Class attribute '{attr_name}' of type {type(arg).__name__} isn't of type Arg. "
                "Arguments must be annotated with '... = arg(...)'."
            )

        args, kwargs = _build_add_argument_args(attr_name, annotation, arg)

        # print(f"Adding argument: {args} {kwargs}")
        parser.add_argument(*args, **kwargs)


def _build_add_argument_args(
    python_arg_name: str,
    annotation: TypeAnnotation,
    arg: Arg,
) -> Tuple[List[str], Dict[str, Any]]:

    help = arg.help
    if help is not None and help is not argparse.SUPPRESS and not arg.auto_default_help:
        help = DefaultHelpFormatter.Unformatted(help)

    kwargs: Dict[str, Any] = {
        "help": help,
    }

    # Unwrap optionals
    underlying_if_optional = annotation.get_underlying_if_optional()
    if underlying_if_optional is not None:
        is_optional = True
        annotation = underlying_if_optional
    else:
        is_optional = False

    # Unwrap collections
    underlying_if_list = annotation.get_underlying_if_list()
    if underlying_if_list is not None:
        is_collection = True
        annotation = underlying_if_list
        # TODO: How should we handle e.g. List[bool]?

        # Sanity checks:
        if arg.nargs_with_default() == "+" and is_optional:
            raise AssertionError("An argument with nargs='+' must not be optional")

    else:
        is_collection = False

    # Determine is_required
    if annotation.is_bool:
        is_required = False
    else:
        if is_optional or arg.has_default():
            is_required = False
        else:
            is_required = True

    # Note that argparse forbids setting 'required' at all for positional args,
    # so we must omit it if false.
    if is_required and not arg.positional:
        kwargs["required"] = True

    # Value handling
    if annotation.is_bool:
        if arg.has_default():
            default_value = arg.resolve_default()
            if default_value is True:
                kwargs["action"] = "store_false"
            elif default_value is False:
                kwargs["action"] = "store_true"
            else:
                raise RuntimeError(f"Invalid default for bool '{default_value}'")
        else:
            kwargs["action"] = "store_true"

    else:
        # We must not declare 'type' for boolean switches, which have an action instead.
        if arg.type is not None:
            kwargs["type"] = arg.type
        else:
            type_converter = annotation.get_underlying_type_converter()
            if type_converter is not None:
                kwargs["type"] = type_converter

        if arg.has_default():
            default_value = arg.resolve_default()
            kwargs["default"] = default_value

            # Argparse requires positionals with defaults to have nargs="?"
            # Note that for list-like (real nargs) arguments that happens to have a default
            # (a list as well), the nargs value will be overwritten below.
            if arg.positional:
                kwargs["nargs"] = "?"

        allowed_values_if_literal = annotation.get_allowed_values_if_literal()
        if allowed_values_if_literal is not None:
            kwargs["choices"] = Choices(*allowed_values_if_literal)

        allowed_values_if_enum = annotation.get_allowed_values_if_enum()
        if allowed_values_if_enum is not None:
            kwargs["choices"] = Choices(*allowed_values_if_enum)

        if arg.dynamic_choices is not None:
            kwargs["choices"] = Choices(*arg.dynamic_choices())

    # Nargs handling
    if is_collection:
        kwargs["nargs"] = arg.nargs_with_default()

    # Name handling
    cli_arg_name = python_arg_name.replace("_", "-")
    name_or_flags: List[str]

    if arg.positional:
        # Note that argparse does not allow to specify the 'dest' for positional arguments.
        # We have to rely on the fact the the hyphenated version of the name gets converted
        # back to exactly our `python_attr_name` as the internal dest, but that should
        # normally be the case.
        name_or_flags = [cli_arg_name]

    else:
        if len(arg.flags) > 0:
            if not all(flag.startswith("-") for flag in arg.flags):
                raise ValueError(
                    f"Invalid flags: {arg.flags}. All flags should start with '-'. "
                    "A positional argument can be created by setting `positional=True`."
                )
            name_or_flags = list(arg.flags)

            # Automatically add the long name if the user only specifies the short flag,
            # but only if the original name is more than 1 char.
            if all(len(flag) == 2 for flag in arg.flags) and len(python_arg_name) > 1:
                name_or_flags += [f"--{cli_arg_name}"]
        else:
            name_or_flags = [f"--{cli_arg_name}"]

        kwargs["dest"] = python_arg_name

    return name_or_flags, kwargs


def _to_string(args_or_group: ArgsOrGroup) -> str:
    if isinstance(args_or_group, type):
        return args_or_group.__name__
    else:
        return str(args_or_group)


def _install_argcomplete_if_available(parser: ArgparseParser) -> None:
    try:
        import argcomplete  # pyright: ignore

        argcomplete.autocomplete(parser)
    except ImportError:
        pass
