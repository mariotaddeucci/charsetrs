"""
Charset Normalizer RS - A Python library with Rust bindings for charset detection
"""

from charset_normalizer_rs._internal import CharsetMatch
from charset_normalizer_rs._internal import from_path as _from_path_internal

__all__ = ["from_path", "CharsetMatch"]
__version__ = "0.1.0"


class CharsetMatches:
    """Container for charset detection results, mimicking charset_normalizer API"""

    def __init__(self, match: CharsetMatch):
        self._match = match

    def best(self):
        """Return the best charset match"""
        return self._match

    def __iter__(self):
        """Allow iteration over matches"""
        yield self._match

    def __len__(self):
        return 1

    def __getitem__(self, index):
        if index == 0:
            return self._match
        raise IndexError("CharsetMatches index out of range")


def from_path(path):
    """
    Detect charset and language from a file path.
    Returns a CharsetMatches object with a best() method.

    Compatible with charset_normalizer's from_path function.
    """
    match = _from_path_internal(str(path))
    return CharsetMatches(match)
