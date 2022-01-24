"""
Slightly improved version:
- Instead of using the __origin__ heuristic, perform isinstance check against the
  underlying instance (typing.GenericMeta in Python 3.6, and typing._GenericAlias
  in modern Python versions)
- Use a type guard to avoid repeated `# type: ignore`s.

Downsides:
- Depends on typing_extensions for the type guard.
- For some reason, mypy doesn't like the typing._GenericAlias type, even in the
  Python versions that should have it. This part can be easily type ignored
  though.
"""

import sys
import typing
from typing import List
from typing_extensions import TypeGuard


if sys.version_info[:2] < (3, 7):

    def is_generic_type(cls: object) -> TypeGuard[type]:
        return isinstance(cls, typing.GenericMeta)

else:

    def is_generic_type(cls: object) -> TypeGuard[type]:
        return isinstance(cls, typing._GenericAlias)  # type: ignore


def func_required_some_type(some_type: type) -> None:
    print(f"Got type: {some_type}")


def func_taking_any(x: object) -> None:
    if isinstance(x, type) or is_generic_type(x):
        # This part is much nicer now, because `x` really is `type` here.
        func_required_some_type(x)


func_required_some_type(str)
func_required_some_type(int)
func_required_some_type(List[str])

func_taking_any(str)
func_taking_any(int)
func_taking_any(List[str])
