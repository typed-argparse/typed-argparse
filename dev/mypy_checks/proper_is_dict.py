# https://stackoverflow.com/questions/58723802/what-python-type-annotation-to-represent-generic-type-class
from typing import Dict, List


def is_dict(cls: type) -> bool:
    if cls is dict:
        return True
    elif hasattr(cls, "__origin__"):
        origin = getattr(cls, "__origin__")
        return bool(origin == dict) or bool(origin == Dict)
    return False


assert not is_dict(int)
assert not is_dict(str)
assert not is_dict(List[int])
assert is_dict(dict)
assert is_dict(Dict[int, int])
