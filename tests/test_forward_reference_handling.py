"""
When working with type annotations we have to be careful regarding forward references,
i.e., quoted usages of "SomeType" or usage of `from __future__ import annotations` on user site.

The essential step is to use `get_type_hints(cls)` instead of just `cls.__annotations__` to
resolve the strings to actual type hints.

But there still is the issue that `get_type_hints` may not be able to "see" types that are
locally defined, resulting in "NameError: name 'SomeType' is not defined". The general work-around
is to pass `localns` to `get_type_hints`. See e.g.:

- https://github.com/python/typing/issues/797
- https://bugs.python.org/issue42829
- https://stackoverflow.com/questions/76325603/evaluating-forward-references-with-typing-get-type-hints-in-python-for-a-class-d

However that is not really feasible if the lookup of the annotations happens in a different context
compared to where the type is defined. In general we probably cannot simply pass the entire `locals()`
of where the type is defined into the context where the type is used.
"""

from __future__ import annotations

import argparse
from enum import Enum
from typing import Optional

import typed_argparse as tap

from ._testing_utils import parse


def test_basic() -> None:
    class Args(tap.TypedArgs):
        foo: str

    args_namespace = argparse.Namespace(foo="foo")
    args = Args.from_argparse(args_namespace)
    assert args.foo == "foo"


def test_parser() -> None:
    class Args(tap.TypedArgs):
        foo: Optional[str]

    def run(arg: Args) -> None:
        ...

    tap.Parser(Args).bind(run).run(raw_args=[])


def test_locally_defined_enum() -> None:
    class MyEnum(str, Enum):
        foo = "foo"
        bar = "bar"

        def __repr__(self) -> str:
            return self.name

    class Args(tap.TypedArgs):
        my_enum: MyEnum

    # We have to account for the possibility that parsing happens in a different `locals()`
    # context that does not see nested types.
    args = parse(Args, ["--my-enum", "foo"])
    assert args.my_enum == MyEnum.foo
