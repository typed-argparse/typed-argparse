from __future__ import annotations

from typed_argparse import Binding, Parser, SubParser, SubParserGroup, TypedArgs
from typed_argparse.parser import App


def is_app_str_int(app: App[str | int]) -> None:
    ...


def is_app_str(app: App[str]) -> None:
    ...


def is_app_int(app: App[int]) -> None:
    ...


def is_app_none(app: App[None]) -> None:
    ...


def typecheck_bindings() -> None:
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

    def check1() -> None:
        app = parser.bind(Binding(FooArgs, foo), Binding(BarArgs, bar))
        reveal_type(app)
        is_app_str_int(app)
        is_app_str(app)  # type: ignore # must not type match
        is_app_int(app)  # type: ignore # must not type match
        is_app_none(app)  # type: ignore # must not type match

    def check2() -> None:
        app = parser.bind(foo, bar)
        reveal_type(app)
        is_app_str_int(app)
        is_app_str(app)  # type: ignore # must not type match
        is_app_int(app)  # type: ignore # must not type match
        is_app_none(app)  # type: ignore # must not type match
