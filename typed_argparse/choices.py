from typing import Any, List


class Choices(List[Any]):
    """
    Work-around for Python bug: https://bugs.python.org/issue27227

    Inspired by: https://bugs.python.org/issue9625#msg347742
    """

    def __new__(cls, *args: object) -> "Choices":
        x = list.__new__(cls, *args)
        return x

    def __init__(self, *args: object) -> None:
        super().__init__(args)

    def __contains__(self, item_or_items: object) -> bool:
        # Notes:
        # - When argparse passes in the args that are externally specified,
        #   they get passed in one-by-one, i.e., item_or_items is a single element.
        #   Argparse internally collects the elements into a list.
        # - When argparse passes in the `default` value, it is passed in as is.
        #   Argparse doesn't collect multiple elements into a list in this case.
        #   Since the __contains__ function can only return whether this passed
        #   in default is valid, all we can do is to iterate over its contents
        #   and check them against the allowed values. If all are valid, we
        #   return True, so that the default value gets accepted. Note that it
        #   is crucial that the passed in default is a list/tuple. If it is a
        #   single element, we have to accept it as well due to the single
        #   element handling of externally passed in values, and there is no way
        #   to detect the default isn't a list.

        if isinstance(item_or_items, list) or isinstance(item_or_items, tuple):
            items = item_or_items
        else:
            items = [item_or_items]

        return all(list.__contains__(self, item) for item in items)
