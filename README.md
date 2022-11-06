# typed_argparse

💡 write type-safe and elegant CLIs with a clear separation of concerns.

[![PyPI version](https://badge.fury.io/py/typed-argparse.svg)](https://badge.fury.io/py/typed_argparse)
[![Build Status](https://github.com/typed-argparse/typed-argparse/workflows/ci/badge.svg)](https://github.com/typed-argparse/typed-argparse/actions?query=workflow%3Aci)
[![codecov](https://codecov.io/gh/typed-argparse/typed-argparse/branch/master/graph/badge.svg?token=6I98R2661Z)](https://codecov.io/gh/typed-argparse/typed-argparse)
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

- Argument parsing based on type annotation (including runtime validation, and support for many common types)
- Clear separation of concern between argument parsing and business logic.
- Support for super-low-latency shell auto-completions.
- Great for [writing sub-command CLIs](https://typed-argparse.github.io/typed-argparse/high_level_api/#sub-commands).
- Very lightweight.
- No dependencies.
- Fully typed, no extra type stubs required.
- Offers both a [high-level](https://typed-argparse.github.io/typed-argparse/high_level_api.md) and a [low-level](https://typed-argparse.github.io/typed-argparse/low_level_api.md) API.
  The high-level API generally requires less code to write, is fully based on type annotations, and is the preferred way for writing new CLIs.
  The low-level API is mainly a low-effort migration path for incorporating type-safety into existing CLIs based on `argparse`.


## Install

```console
$ pip install typed-argparse
```

The only requirement is a modern Python (3.6+).


## Basic Usage

```python
import typed_argparse as tap


# 1. Argument definition
class Args(tap.TypedArgs):
    my_arg: str = tap.arg(help="some help")
    number_a: int = tap.arg(default=42, help="some help")
    number_b: Optional[int] = tap.arg(help="some help")
    verbose: bool = tap.arg(help="some help")
    names: List[str] = tap.arg(help="some help")


# 2. Business logic
def runner(args: Args):
    print(f"Running my app with args:\n{args}")


# 3. Bind & run argument definition + business logic
def main() -> None:
    tap.Parser(Args).bind(runner).run()
```


## Documentation

See [full documentation](https://typed-argparse.github.io/typed-argparse/).


## Changes

See [change log](CHANGES.md).


## License

This project is licensed under the terms of the [MIT license](LICENSE).
