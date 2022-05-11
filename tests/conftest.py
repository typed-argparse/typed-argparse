import sys
from typing import List

collect_ignore: List[str] = []

if sys.version_info < (3, 7):
    collect_ignore.append("test_future_annotations.py")
