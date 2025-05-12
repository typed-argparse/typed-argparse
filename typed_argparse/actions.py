import argparse
from gettext import gettext, ngettext
from typing import Sequence, Type


class NamedTupleAction(argparse.Action):
    def __init__(
        self, option_strings: list[str], dest: str, type: Type, nargs=None, metavar=None, **kwargs
    ):
        assert metavar is None, "metavar is not None"

        is_list = nargs is not None
        if not is_list:
            nargs = 1

        if isinstance(nargs, int):
            metavar = tuple((field.upper() for _ in range(nargs) for field in type._fields))
            nargs = len(metavar)
        else:
            metavar = " ".join((field.upper() for field in type._fields))

        super().__init__(option_strings, dest, type=None, nargs=nargs, metavar=metavar, **kwargs)

        self._type = type
        self.is_list = is_list

    def field_type_at_index(self, index: int):
        field = self._type._fields[index]
        return self._type.__annotations__[field]

    def parse_value(self, index: int, value: str):
        field_type = self.field_type_at_index(index)
        try:
            return field_type(value)
        except (TypeError, ValueError):
            name = getattr(field_type, "__name__", repr(field_type))
            args = {"type": name, "value": value}
            msg = gettext("invalid %(type)s value: %(value)r")
            raise argparse.ArgumentError(self, msg % args)

    def parse_values(self, values: Sequence[str]):
        return self._type(*(self.parse_value(i, value) for i, value in enumerate(values)))

    def parse(self, values: Sequence[str]):
        if self.is_list:
            n = len(self._type._fields)
            values_len = len(values)
            if values_len % n != 0:
                msg = gettext("expected at least %s arguments") % (
                    values_len + n - (values_len % n)
                )
                raise argparse.ArgumentError(self, msg)

            return [self.parse_values(values[i : i + n]) for i in range(0, values_len, n)]
        else:
            return self.parse_values(values)

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(values, list):
            raise ValueError(values)

        setattr(namespace, self.dest, self.parse(values))
