# typed_argparse


💡 type-safe args for argparse without much refactoring.


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

1. Add a type `MyArgs(TypedArgs)` that inherits from `TypedArgs` and fill it with type annotations.
2. Wrap the result of e.g. your `parse_args` function with `MyArgs`.
3. That's it, enjoy IDE auto-completion and strong type safety 😀.


## Features

- Implicit runtime validation to ensure type annotations are correct
- Very lightweight
- No dependencies
- Fully typed, no stubs required


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
class MyArgs(TypedArgs):
    foo: str
    num: Optional[int]
    files: List[str]


def parse_args(args: List[str] = sys.argv[1:]) -> MyArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", type=str, required=True)
    parser.add_argument("--num", type=int)
    parser.add_argument("--files", type=str, nargs="*")
    # Step 2: Wrap the plain argparser result with your type.
    return MyArgs(parser.parse_args(args))


def main() -> None:
    args = parse_args(["--foo", "foo", "--num", "42", "--files", "a", "b", "c"])
    # Step 3: Done, enjoy IDE auto-completion and strong type safety
    assert args.foo == "foo"
    assert args.num == 42
    assert args.files == ["a", "b", "c"]


if __name__ == "__main__":
    main()
```

**Notes**:

- `typed_argparse` validates that no attributes from the type definition are missing, and that
  no unexpected extra types are present in the `argparse.Namespace` object. It also validates
  the types at runtime. Therefore, if the `MyArgs(args)` doesn't throw a `TypeError` you can
  be sure that your type annotation is correct.
- If you have usages that require access to the raw `argparse.Namespace` object, you can do 
  so by using `args.get_raw_args()`. Note that internal `argparse.Namespace` object isn't
  synced with the `args` data itself, i.e., mutating either of them doesn't mutate the other.
  
  