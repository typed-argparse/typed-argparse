## Motivation

Want to add type annotations to a code base that makes use of `argparse` without refactoring all you CLIs?
`typed_argparse`'s low-level API allows to do that with minimal changes:

1. Add a type `Args(TypedArgs)` that inherits from `TypedArgs` and fill it with type annotations.
2. Wrap the result of e.g. your `parse_args` function with `Args`.
3. That's it, enjoy IDE auto-completion and strong type safety 😀.


!!! Note
    If you plan to write a new CLI from scratch, consider using the [high-level API](high_level_api.md) instead.


## Usage

```python title="basic_usage.py"
--8<-- "examples/low_level_api/basic_usage.py"
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

    # Alternatively:
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

