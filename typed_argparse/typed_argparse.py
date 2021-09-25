import argparse

from typing import List

from . import type_utils

_NoneType = type(None)


class TypedArgs:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

        missing_args: List[str] = []

        for arg_name, type_annotation_any in self.__annotations__.items():
            if arg_name == "get_raw_args" or arg_name == "_args":
                raise TypeError(f"A type must not have an argument called '{arg_name}'")

            type_annotation: type_utils.RawTypeAnnotation = type_annotation_any

            if not hasattr(args, arg_name):
                missing_args.append(arg_name)
            else:
                value: object = getattr(args, arg_name)

                value = type_utils.validate_value_against_type(arg_name, value, type_annotation)

                self.__dict__[arg_name] = value

        # Handle missing args
        if len(missing_args) > 0:
            if len(missing_args) == 1:
                raise TypeError(f"Arguments object is missing argument '{missing_args[0]}'")
            else:
                raise TypeError(f"Arguments object is missing arguments {missing_args}")

        # Handle extra args
        extra_args = sorted(set(args.__dict__.keys()) - set(self.__annotations__.keys()))
        if len(extra_args) > 0:
            if len(extra_args) == 1:
                raise TypeError(
                    f"Arguments object has an unexpected extra argument '{extra_args[0]}'"
                )
            else:
                raise TypeError(f"Arguments object has unexpected extra arguments {extra_args}")

    def get_raw_args(self) -> argparse.Namespace:
        return self._args

    def __repr__(self) -> str:
        key_value_pairs = [f"{k}={repr(v)}" for k, v in self.__dict__.items() if k != "_args"]
        return f"{self.__class__.__name__}({', '.join(key_value_pairs)})"

    def __str__(self) -> str:
        return repr(self)
