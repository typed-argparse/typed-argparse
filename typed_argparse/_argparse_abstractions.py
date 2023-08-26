from __future__ import annotations

import argparse
from typing import Sequence, TypedDict

from typing_extensions import Protocol


class FormatterClass(Protocol):
    def __call__(self, prog: str) -> argparse.HelpFormatter:
        ...


class AddParserKwArgs(TypedDict, total=False):
    help: str | None
    aliases: Sequence[str]
