"""
Having arguments of type "type" is a awkward, because typing.List and others
fail an instance(List, type) check on Python 3.7+. The following has the correct
runtime behavior in Python 3.6, but misbehaves in newer Python versions.

Some references:

- https://stackoverflow.com/questions/58723802/what-python-type-annotation-to-represent-generic-type-class
- https://stackoverflow.com/questions/49171189/whats-the-correct-way-to-check-if-an-object-is-a-typing-generic

"""

from typing import List


def func_required_some_type(some_type: type) -> None:
    print(f"Got type: {some_type}")


def func_taking_any(x: object) -> None:
    if isinstance(x, type):
        func_required_some_type(x)


func_required_some_type(str)
func_required_some_type(int)
func_required_some_type(List[str])

func_taking_any(str)
func_taking_any(int)
func_taking_any(List[str])
