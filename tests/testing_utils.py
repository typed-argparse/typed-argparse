import sys

import pytest

pre_python_10 = pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason="Test is Python version specific, and currently skipped for Python 3.10+",
)


def compare_verbose(actual: str, expected: str) -> None:

    print(f'EXPECTED:\n"""\\\n{expected}"""\n\nACTUAL:\n"""\\\n{actual}"""\n\n')

    assert actual == expected
