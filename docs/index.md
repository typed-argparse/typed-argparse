# typed-argparse

💡 write type-safe and elegant CLIs with a clear separation of concerns.

[![PyPI version](https://badge.fury.io/py/typed-argparse.svg)](https://badge.fury.io/py/typed-argparse)
[![Build Status](https://github.com/typed-argparse/typed-argparse/workflows/ci/badge.svg)](https://github.com/typed-argparse/typed-argparse/actions?query=workflow%3Aci)
[![codecov](https://codecov.io/gh/typed-argparse/typed-argparse/branch/master/graph/badge.svg?token=6I98R2661Z)](https://codecov.io/gh/typed-argparse/typed-argparse)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![mypy](https://img.shields.io/badge/mypy-strict-blue)](http://mypy-lang.org/)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](LICENSE)

---

## Features

- Argument parsing based on type annotation (including runtime validation).
- Support for many common types.
- Clear separation of concern between argument parsing and business logic.
- Support for super-low-latency shell [auto-completions](high_level_api/#auto-completion).
- Great for [writing sub-command CLIs](high_level_api/#sub-commands).
- Very lightweight.
- No dependencies.
- Fully typed itself, no extra type stubs required.
- Offers both a [high-level](high_level_api.md) and a [low-level](low_level_api.md) API.
  The high-level API generally requires less code to write, is fully based on type annotations, and is the preferred way for writing new CLIs.
  The low-level API is mainly a low-effort migration path for incorporating type-safety into existing CLIs based on `argparse`.


## Install

```console
$ pip install typed-argparse
```

The only requirement is a modern Python (3.6+).


## Next step

Continue with [getting started](http://127.0.0.1:8000/high_level_api/#getting-started).