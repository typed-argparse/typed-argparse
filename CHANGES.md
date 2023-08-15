# Changelog

## 0.3.0 WIP

- Make constructor of `TypedArgs` adhere to type semantics of dataclass transform.
- Drop work-around and backports for Python 3.6 and 3.7

## 0.2.11

- Fix regression introduced by `typing_extensions` version 4.6.0+.

## 0.2.10

- Support for `formatter_class` in `Parser`.

## 0.2.9

- Fix issue when parser is used under `from __future__ import annotations` context.

## 0.2.8

- Add support for forwarding help and description to subparser and subparser groups respectively.

## 0.2.7

- Add support for optional list (nargs) arguments.

## 0.2.6

- Update package meta data on PyPI to reflect changed project URL/name.

## 0.2.5

- Support for fuzzy choice matching
- Support for dynamic choices
- Support for dynamic defaults
- Fixed type annotations for nargs

## 0.2.4

- Support for nargs handling
- Renamed subparser API

## 0.2.3

- Support forward standard arguments (like description, epilog, ...) to argparse
- Support for custom type parsers
- Support for common args

## 0.2.2

- Support for argcomplete
- Fix subparser handling
- Flags support

## 0.2.1

- Fix backwards compatibility of `TypedArgs` constructor

## 0.2.0

- First draft of app system

## 0.1.x

Initial MVP phase, no changes tracked.
