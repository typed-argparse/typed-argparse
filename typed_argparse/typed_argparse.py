import argparse

from typing import List, Union

from . import type_utils

_NoneType = type(None)


class TypedArgs:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

        missing_fields: List[str] = []

        for name, argument_type in self.__annotations__.items():
            if name == "get_raw_args":
                raise TypeError("A type must not have an argument called 'get_raw_args'")

            if not hasattr(args, name):
                missing_fields.append(name)
            else:
                x = getattr(args, name)

                underlying_type = None
                is_optional = False

                if type_utils.is_list(argument_type):
                    underlying_type = type_utils.get_underlying_type_of_list(argument_type)
                    argument_type = list

                if hasattr(argument_type, "__origin__"):
                    if argument_type.__origin__ is Union and len(argument_type.__args__) == 2:
                        if argument_type.__args__[0] == _NoneType:
                            is_optional = True
                            argument_type = argument_type.__args__[1]
                        elif argument_type.__args__[1] == _NoneType:
                            is_optional = True
                            argument_type = argument_type.__args__[0]

                if is_optional:
                    if not isinstance(x, argument_type) and not (x is None):
                        raise TypeError(
                            f"Type of argument '{name}' should be "
                            f"Optional[{argument_type.__name__}], but is "
                            f"{type(x).__name__}"
                        )

                else:
                    if not isinstance(x, argument_type):
                        raise TypeError(
                            f"Type of argument '{name}' should be "
                            f"{argument_type.__name__}, but is "
                            f"{type(x).__name__}"
                        )

                if underlying_type is not None and hasattr(x, "__iter__"):
                    if not all(isinstance(element, underlying_type) for element in x):
                        raise TypeError(
                            f"Not all elements of argument '{name}' are of type "
                            f"{underlying_type.__name__}"
                        )

                self.__dict__[name] = x

        # Handle missing fields
        if len(missing_fields) > 0:
            if len(missing_fields) == 1:
                raise TypeError(f"Arguments object is missing argument '{missing_fields[0]}'")
            else:
                raise TypeError(f"Arguments object is missing arguments {missing_fields}")

        # Handle extra fields
        extra_fields = sorted(set(args.__dict__.keys()) - set(self.__annotations__.keys()))
        if len(extra_fields) > 0:
            if len(extra_fields) == 1:
                raise TypeError(
                    f"Arguments object has an unexpected extra argument '{extra_fields[0]}'"
                )
            else:
                raise TypeError(
                    f"Arguments object has an unexpected extra arguments {extra_fields}"
                )

    def get_raw_args(self) -> argparse.Namespace:
        return self._args
