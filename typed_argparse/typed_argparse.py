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

        # Handle missing fields
        if len(missing_fields) > 0:
            if len(missing_fields) == 1:
                raise TypeError(f"Arguments object is missing attribute '{missing_fields[0]}'")
            else:
                raise TypeError(f"Arguments object is missing attributes {missing_fields}")

        # Handle extra fields
        extra_fields = list(set(args.__dict__.keys()) - set(self.__annotations__.keys()))
        if len(extra_fields) > 0:
            if len(extra_fields) == 1:
                raise TypeError(
                    f"Arguments object has an unexpected extra attribute '{extra_fields[0]}'"
                )
            else:
                raise TypeError(
                    f"Arguments object has an unexpected extra attributes {extra_fields}"
                )
