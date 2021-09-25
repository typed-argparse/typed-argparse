import argparse

from collections.abc import Iterable
from typing import List

from . import type_utils

_NoneType = type(None)


class TypedArgs:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

        missing_args: List[str] = []

        for name, argument_type_any in self.__annotations__.items():
            if name == "get_raw_args" or name == "_args":
                raise TypeError(f"A type must not have an argument called '{name}'")

            argument_type: object = argument_type_any

            if not hasattr(args, name):
                missing_args.append(name)
            else:
                x: object = getattr(args, name)

                # Handle optional first to handle Optional[List[T]] properly
                optional_check = type_utils.check_for_optional(argument_type)
                if optional_check.is_optional:
                    argument_type = optional_check.underlying_type

                list_check = type_utils.check_for_list(argument_type)
                if list_check.is_list:
                    argument_type = list
                    # Special handling for lists: Coerce empty lists automatically if not optional
                    if x is None and not optional_check.is_optional:
                        x = []

                type_wrapper = type_utils.get_type_wrapper(argument_type)

                if optional_check.is_optional:
                    if not type_wrapper.validate(x) and not (x is None):
                        raise TypeError(
                            f"Type of argument '{name}' should be "
                            f"Optional[{type_wrapper.name}], but is "
                            f"{type(x).__name__}"
                        )

                else:
                    if not type_wrapper.validate(x):
                        raise TypeError(
                            f"Type of argument '{name}' should be "
                            f"{type_wrapper.name}, but is "
                            f"{type(x).__name__}"
                        )

                if list_check.underlying_type is not None and isinstance(x, Iterable):
                    if not all(isinstance(element, list_check.underlying_type) for element in x):
                        raise TypeError(
                            f"Not all elements of argument '{name}' are of type "
                            f"{list_check.underlying_type.__name__}"
                        )

                self.__dict__[name] = x

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
