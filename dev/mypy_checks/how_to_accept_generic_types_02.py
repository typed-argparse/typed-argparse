"""
The easiest work-around may be:
- Check for "__origin__" as a heuristic to have an object that may be a typing.XXX type.
- Add a type ignore at the point where the heuristic is applied.
"""

from typing import List


def func_required_some_type(some_type: type) -> None:
    print(f"Got type: {some_type}")


def func_taking_any(x: object) -> None:
    if isinstance(x, type) or hasattr(x, "__origin__"):
        func_required_some_type(x)  # type: ignore


func_required_some_type(str)
func_required_some_type(int)
func_required_some_type(List[str])

func_taking_any(str)
func_taking_any(int)
func_taking_any(List[str])
