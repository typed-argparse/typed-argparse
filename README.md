# typed_argparse


💡 type-safe args for argparse without much refactoring.

<!--
💡 `typed_argparse` allows to write type-safe and elegant CLIs with a clear separation of concerns.
-->

[![PyPI version](https://badge.fury.io/py/typed-argparse.svg)](https://badge.fury.io/py/typed_argparse)
[![Build Status](https://github.com/bluenote10/typed_argparse/workflows/ci/badge.svg)](https://github.com/bluenote10/typed_argparse/actions?query=workflow%3Aci)
[![codecov](https://codecov.io/gh/bluenote10/typed_argparse/branch/master/graph/badge.svg?token=6I98R2661Z)](https://codecov.io/gh/bluenote10/typed_argparse)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![mypy](https://img.shields.io/badge/mypy-strict-blue)](http://mypy-lang.org/)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](LICENSE)


<br>

---

<br>

## Motivation

Want to add type annotations to a code base that makes use of `argparse` without refactoring all you CLIs?
`typed_argparse` allows to do that with minimal changes:

1. Add a type `Args(TypedArgs)` that inherits from `TypedArgs` and fill it with type annotations.
2. Wrap the result of e.g. your `parse_args` function with `Args`.
3. That's it, enjoy IDE auto-completion and strong type safety 😀.


## Features

- Implicit runtime validation to ensure type annotations are correct
- Support for common types (Optional, List, Literal, Enum, Union, and regular classes)
- Convenience functionality to map Literal/Enum to choices
- Convenience functionality to map Union to subcommands
- Very lightweight
- No dependencies
- Fully typed, no extra type stubs required


## Install

```console
$ pip install typed-argparse
```

The only requirement is a modern Python (3.6+).


## Usage

```python
import argparse
import sys
from typing import List, Optional
from typed_argparse import TypedArgs


# Step 1: Add an argument type.
class Args(TypedArgs):
    foo: str
    num: Optional[int]
    files: List[str]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=str, required=True)
    parser.add_argument("--num", type=int)
    parser.add_argument("--files", type=str, nargs="*")
    # Step 2: Wrap the plain argparser result with your type.
    return Args.from_argparse(parser.parse_args(args))


def main() -> None:
    args = parse_args()
    # Step 3: Done, enjoy IDE auto-completion and strong type safety
    assert args.foo == "foo"
    assert args.num == 42
    assert args.files == ["a", "b", "c"]


if __name__ == "__main__":
    main()
```


`typed_argparse` validates that no attributes from the type definition are missing, and that
no unexpected extra types are present in the `argparse.Namespace` object. It also validates
the types at runtime. Therefore, if the `Args.from_argparse(args)` doesn't throw a `TypeError` you can
be sure that your type annotation is correct.


## Feature Examples

### Convenience functionality to map Literal/Enum to choices

When defining arguments that should be limited to certain values, a natural choice for the corresponding type is to use either `Literal` or `Enum`.
On argparse side, the corresponding setting is to specify the `choices=...` parameter.
In order to have a single source of truth (i.e., avoid having to specify the values twice), it is possible to use `TypedArgs.get_choices_from()`.
For instance:

```python
class Args(TypedArgs):
    mode: Literal["a", "b", "c"]


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=Args.get_choices_from("mode"),
    )
    return Args.from_argparse(parser.parse_args(args))
```

This makes sure that `choices` is always in sync with the values allowed by `Args.mode`.
The same works when using `mode: SomeEnum` where `SomeEnum` is an enum inheriting `enum.Enum`.


```python
class MyEnum(Enum):
    a = "a"
    b = "b"
    c = "c"


class Args(TypedArgs):
    mode: MyEnum


def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=MyEnum,
        required=True,
        choices=Args.get_choices_from("mode"),
    )
    return Args.from_argparse(parser.parse_args(args))
```


### Support for Union (useful for subcommand parsing)

When implementing multi command CLIs, the various subparsers can often have completely different arguments.
In terms of the type system such arguments are best modelled as a `Union` type.
For instance, consider a CLI that has two modes `foo` and `bar`.
In the `foo` mode, we want a `--file` arg, but in the `bar` mode, we want e.g. a `--src` and `--dst` args.
We also want some shared args, like `--verbose`.
This can be achieved by modeling the types as:

```python
from typed_argparse import TypedArgs, WithUnionType


class CommonArgs(TypedArgs):
    verbose: bool


class ArgsFoo(CommonArgs):
    mode: Literal["foo"]
    file: str


class ArgsBar(CommonArgs):
    mode: Literal["bar"]
    src: str
    dst: str


Args = Union[ArgsFoo, ArgsBar]
```

On parsing side, `WithUnionType[Args].validate(...)` can be used to parse the arguments into a type union:

```python
def parse_args(args: List[str] = sys.argv[1:]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Verbose")
    subparsers = parser.add_subparsers(
        help="Available sub commands",
        dest="mode",
        required=True,
    )

    parser_foo = subparsers.add_parser("foo")
    parser_foo.add_argument("file", type=str)

    parser_bar = subparsers.add_parser("bar")
    parser_bar.add_argument("--src", required=True)
    parser_bar.add_argument("--dst", required=True)

    return WithUnionType[Args].validate(parser.parse_args(args))
```

Type checkers like mypy a pretty good at handling such "tagged unions". Usage could look like:

```python
def main() -> None:
    args = parse_args()

    if args.mode == "foo":
        # In this branch, mypy knows (only) these fields (and their types)
        print(args.file, args.verbose)

    if args.mode == "bar":
        # In this branch, mypy knows (only) these fields (and their types)
        print(args.src, args.dst, args.verbose)

    # Alteratively:
    if isinstance(args, ArgsFoo):
        # It's an ArgsFoo
        ...
    if isinstance(args, ArgsBar):
        # It's an ArgsBar
        ...
```


### Work-around for common argparse limitation

A known limitation ([bug report](https://bugs.python.org/issue9625),
[SO question 1](https://stackoverflow.com/questions/41750896/python-argparse-type-inconsistencies-when-combining-choices-nargs-and-def/41751730#41751730),
[SO question 2](https://stackoverflow.com/questions/57739309/argparse-how-to-allow-empty-list-with-nargs-and-choices))
of argparse is that it is not possible to combine a positional `choices` parameters with `nargs="*"` and an list-like default.
This may sounds exotic, but isn't such a rare use case in practice.
Consider for instance a positional `actions` argument that should take the values "eat" and "sleep" and allow for arbitrary sequences "eat eat sleep eat ...".
The library provides a small work-around wrapper class `Choices` that allows to work-around this argparse limitation:


```python
from typed_argparse import Choices

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "actions",
        nargs="*",
        choices=Choices("eat", "sleep"),
        default=[],
    )
```

`TypedArgs.get_choices_from()` internally uses this wrapper, i.e., it automatically solves the limitation.

