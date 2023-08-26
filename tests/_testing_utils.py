import argparse
import sys
from contextlib import contextmanager
from typing import Generator, Optional

import pytest

pre_python_10 = pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason="Test is Python version specific, and currently skipped for Python 3.10+",
)


def compare_verbose(actual: str, expected: str) -> None:

    print(f'EXPECTED:\n"""\\\n{expected}"""\n\nACTUAL:\n"""\\\n{actual}"""\n\n')

    assert actual == expected


class ArgparseErrorWrapper:
    def __init__(self) -> None:
        self._error: Optional[argparse.ArgumentError] = None

    @property
    def error(self) -> argparse.ArgumentError:
        assert self._error is not None
        return self._error

    @error.setter
    def error(self, value: argparse.ArgumentError) -> None:
        self._error = value


@contextmanager
def argparse_error() -> Generator[ArgparseErrorWrapper, None, None]:
    # Inspired by:
    # https://stackoverflow.com/a/67107620/1804173

    wrapper = ArgparseErrorWrapper()

    with pytest.raises(SystemExit) as e:
        yield wrapper

    assert isinstance(e.value.__context__, argparse.ArgumentError)
    wrapper.error = e.value.__context__
