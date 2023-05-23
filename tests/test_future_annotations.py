"""
This test check compatibility with `from __future__ import annotations` on user site.

When using annotations, the __annotations__ behave differently and only contain strings
instead of actual types, which needs to be taken into consideration.
"""

from __future__ import annotations

import argparse
from typing import Optional

import typed_argparse as tap


def test_basic() -> None:
    class Args(tap.TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


# Supporting moving this type from top-level to nested in the test case is probably
# impossible due to, right?
# https://github.com/python/typing/issues/797
class Args(tap.TypedArgs):
    foo: Optional[str]


def test_parser() -> None:
    def run(arg: Args) -> None:
        ...

    tap.Parser(Args).bind(run).run(raw_args=[])
