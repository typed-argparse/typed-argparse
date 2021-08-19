import argparse

from typing import List


class TypedArgs:
    def __init__(self, args: argparse.Namespace):
        self._args = args

        missing_fields: List[str] = []

        for name, annotation in self.__annotations__.items():

            if not hasattr(args, name):
                missing_fields.append(name)
            else:
                self.__dict__[name] = getattr(args, name)

        if len(missing_fields) > 0:
            if len(missing_fields) == 1:
                raise TypeError(f"Arguments object is missing attribute '{missing_fields[0]}'")
            else:
                raise TypeError(f"Arguments object is missing attributes {missing_fields}")
