import argparse
import re
import sys
from contextlib import contextmanager
from typing import Generator, Optional

import pytest

pre_python_3_10 = pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason="Test is Python version specific, and currently skipped for Python 3.10+",
)

starting_with_python_3_10 = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="Test is Python version specific, requiring Python 3.10+",
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


def remove_ansii_escape_sequences(s: str) -> str:
    """Return the string with all ANSI escape sequences removed."""

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    #                          ^^A^   ^^^^B^^^^ ^^^^C^^^^^^^^^^^^^^
    # A: ESC character which starts ANSI sequences
    # B: single character command, like ESC E (next line)
    # C: control sequence command, starts with ESC [, like \x1b[31m for red
    return ansi_escape.sub("", s)
