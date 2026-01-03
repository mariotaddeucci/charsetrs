"""
Charset Normalizer RS - A Python library with Rust bindings for charset detection
"""

from charset_normalizer_rs._internal import CharsetMatch
from charset_normalizer_rs._internal import from_path as _from_path_internal

__all__ = ["from_path", "CharsetMatch", "detect_encoding", "read_file_with_encoding"]
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
    Detect charset from a file path.
    Returns a CharsetMatches object with a best() method.

    Compatible with charset_normalizer's from_path function.
    """
    match = _from_path_internal(str(path))
    return CharsetMatches(match)


def detect_encoding(path):
    """
    Detect the encoding of a file.
    Returns the encoding name as a string.

    Args:
        path: Path to the file to detect encoding

    Returns:
        str: The detected encoding name (e.g., 'utf_8', 'cp1252')
    """
    match = _from_path_internal(str(path))
    return match.encoding


def read_file_with_encoding(path, encoding):
    """
    Read a file with a specific encoding.

    Args:
        path: Path to the file to read
        encoding: Encoding name to use (e.g., 'utf-8', 'latin-1')

    Returns:
        str: The decoded content of the file

    Raises:
        IOError: If file cannot be read
        LookupError: If encoding is invalid
    """
    # Normalize encoding name
    encoding_normalized = encoding.lower().replace("-", "_")

    # Map common encoding names to Python codec names
    encoding_map = {
        "utf_8": "utf-8",
        "utf8": "utf-8",
        "utf_16": "utf-16",
        "utf16": "utf-16",
        "utf_16_le": "utf-16-le",
        "utf_16_be": "utf-16-be",
        "utf_16le": "utf-16-le",
        "utf_16be": "utf-16-be",
        "utf16le": "utf-16-le",
        "utf16be": "utf-16-be",
        "iso_8859_1": "latin-1",
        "latin_1": "latin-1",
        "latin1": "latin-1",
        "windows_1252": "cp1252",
        "cp1252": "cp1252",
        "windows_1256": "cp1256",
        "cp1256": "cp1256",
        "windows_1255": "cp1255",
        "cp1255": "cp1255",
        "windows_1253": "cp1253",
        "cp1253": "cp1253",
        "windows_1251": "cp1251",
        "cp1251": "cp1251",
        "windows_1254": "cp1254",
        "cp1254": "cp1254",
        "windows_1250": "cp1250",
        "cp1250": "cp1250",
        "windows_949": "cp949",
        "cp949": "cp949",
        "big5": "big5",
        "gbk": "gbk",
        "gb2312": "gb2312",
        "shift_jis": "shift_jis",
        "euc_jp": "euc_jp",
        "euc_kr": "euc_kr",
        "mac_cyrillic": "mac_cyrillic",
        "mac_roman": "mac_roman",
        "koi8_r": "koi8_r",
        "koi8_u": "koi8_u",
        "ascii": "ascii",
        "us_ascii": "ascii",
    }

    python_encoding = encoding_map.get(encoding_normalized, encoding)

    try:
        with open(path, encoding=python_encoding, errors="strict") as f:
            return f.read()
    except (UnicodeDecodeError, LookupError) as e:
        raise ValueError(f"Cannot decode file with encoding '{encoding}': {str(e)}") from e
