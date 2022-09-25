from typing import Any, NamedTuple, Optional


class Param(NamedTuple):
    required: bool
    default: object
    help: Optional[str]


def param(
    required: bool = False,
    default: object = None,
    help: Optional[str] = None,
) -> Any:
    return Param(required=required, default=default, help=help)
