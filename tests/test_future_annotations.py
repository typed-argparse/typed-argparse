"""
This test check compatibility with `from __future__ import annotations` on user site.

When using annotations, the __annotations__ behave differently and only contain strings
instead of actual types, which needs to be taken into consideration.
"""

from __future__ import annotations  # type: ignore # noqa # to silence mypy under Python 3.6

import argparse

from typed_argparse import TypedArgs


def test_basic() -> None:
    class MyArgs(TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = MyArgs(args_namespace)
    assert args.foo == "foo"
