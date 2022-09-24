from typing import Any, NamedTuple, Optional


class Param(NamedTuple):
    required: bool
    help: Optional[str]


def param(
    required: bool = False,
    help: Optional[str] = None,
) -> Any:
    return Param(required=required, help=help)
