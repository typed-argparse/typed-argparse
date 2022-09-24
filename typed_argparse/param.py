from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Param:
    required: bool
    help: Optional[str]


def param(
    required: bool = False,
    help: Optional[str] = None,
) -> Any:
    return Param(required=required, help=help)
