from __future__ import annotations

import argparse
from typing import Optional, Sequence, TypedDict

from typing_extensions import Protocol


class FormatterClass(Protocol):
    def __call__(self, prog: str) -> argparse.HelpFormatter:
        ...


class ArgumentParserKwArgs(TypedDict, total=False):
    # We need to only model the kwargs the are optional on our side,
    # but have a default on argparse side.
    formatter_class: FormatterClass


class AddParserKwArgs(TypedDict, total=False):
    help: str | None
    aliases: Sequence[str]


def create_argparse_parser(
    prog: Optional[str] = None,
    usage: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    add_help: bool = True,
    allow_abbrev: bool = True,
    formatter_class: Optional[FormatterClass] = None,
) -> argparse.ArgumentParser:
    kwargs: ArgumentParserKwArgs = {}
    if formatter_class is not None:
        kwargs["formatter_class"] = formatter_class
    return argparse.ArgumentParser(
        prog=prog,
        usage=usage,
        description=description,
        epilog=epilog,
        add_help=add_help,
        allow_abbrev=allow_abbrev,
        **kwargs,
    )
