from __future__ import annotations

from typing import Any

from typing_extensions import assert_type

from typed_argparse import Binding, Parser, SubParser, SubParserGroup, TypedArgs
from typed_argparse.parser import App


def typecheck_bindings__homogenous__None() -> None:
    class FooArgs(TypedArgs):
        ...

    class BarArgs(TypedArgs):
        ...

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    def foo(foo_args: FooArgs) -> None:
        ...

    def bar(bar_args: BarArgs) -> None:
        ...

    def scope_eager_plain_functions() -> None:
        app = parser.bind(foo, bar)
        assert_type(app, App[None])

    def scope_eager_binding_wrapper() -> None:
        app = parser.bind(Binding(FooArgs, foo), Binding(BarArgs, bar))
        assert_type(app, App[None])

    def scope_lazy_plain_functions() -> None:
        # Fully broken
        app = parser.bind_lazy(lambda: [foo, bar])  # type: ignore[var-annotated, arg-type, return-value]
        assert_type(app, App[Any])

    def scope_lazy_binding_wrapper() -> None:
        # Semi broken
        app = parser.bind_lazy(lambda: [Binding(FooArgs, foo), Binding(BarArgs, bar)])  # type: ignore[return-value] # noqa
        assert_type(app, App[None])


def typecheck_bindings__homogenous__int() -> None:
    class FooArgs(TypedArgs):
        ...

    class BarArgs(TypedArgs):
        ...

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    def foo(foo_args: FooArgs) -> int:
        return 42

    def bar(bar_args: BarArgs) -> int:
        return 42

    def scope_eager_plain_functions() -> None:
        app = parser.bind(foo, bar)
        assert_type(app, App[int])

    def scope_eager_binding_wrapper() -> None:
        app = parser.bind(Binding(FooArgs, foo), Binding(BarArgs, bar))
        assert_type(app, App[int])

    def scope_lazy_plain_functions() -> None:
        # Fully broken
        app = parser.bind_lazy(lambda: [foo, bar])  # type: ignore[var-annotated, arg-type, return-value]
        assert_type(app, App[Any])

    def scope_lazy_binding_wrapper() -> None:
        # Semi broken
        app = parser.bind_lazy(
            lambda: [Binding(FooArgs, foo), Binding(BarArgs, bar)]  # type: ignore[return-value]
        )
        assert_type(app, App[int])


def typecheck_bindings__heterogenous() -> None:
    class FooArgs(TypedArgs):
        ...

    class BarArgs(TypedArgs):
        ...

    parser = Parser(
        SubParserGroup(
            SubParser("foo", FooArgs),
            SubParser("bar", BarArgs),
        )
    )

    def foo(foo_args: FooArgs) -> int:
        return 42

    def bar(bar_args: BarArgs) -> str:
        return "foo"

    def scope_eager_plain_functions() -> None:
        # Semi broken
        app = parser.bind(foo, bar)
        assert_type(app, App[object])

    def scope_eager_binding_wrapper() -> None:
        # Fully broken
        # Cannot infer type argument 1 of "bind" of "Parser"
        app = parser.bind(Binding(FooArgs, foo), Binding(BarArgs, bar))  # type: ignore[misc]
        assert_type(app, App[Any])

    def scope_lazy_plain_functions() -> None:
        # Fully broken
        # Need type annotation for "app"
        app = parser.bind_lazy(lambda: [foo, bar])  # type: ignore[var-annotated, arg-type, return-value]
        assert_type(app, App[Any])

    def scope_lazy_binding_wrapper() -> None:
        # Fully broken
        # Need type annotation for "app"
        app = parser.bind_lazy(
            lambda: [Binding(FooArgs, foo), Binding(BarArgs, bar)],  # type: ignore[var-annotated, arg-type, return-value] # noqa
        )
        assert_type(app, App[Any])
