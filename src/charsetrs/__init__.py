"""
Charsetrs - A Python library with Rust bindings for charset detection
"""

from dataclasses import dataclass
from typing import Literal

from charsetrs._internal import CharsetMatch
from charsetrs._internal import analyse_from_path_stream as _analyse_from_path_stream_internal

__all__ = [
    "analyse",
    "convert",
    "normalize",
    "AnalysisResult",
    "CharsetMatch",
]
__version__ = "0.1.0"


@dataclass(frozen=True)
class AnalysisResult:
    """Result of file analysis containing encoding and newline style information."""

    encoding: str
    newlines: Literal["LF", "CRLF", "CR"]


def analyse(file_path, max_sample_size=None):
    """
    Analyse the encoding and newline style of a file.

    This function uses streaming to analyze files efficiently, making it suitable
    for large files. By default, it reads up to 1MB of the file for analysis.

    Args:
        file_path: Path to the file to analyse (string or Path object)
        max_sample_size: Optional. Maximum number of bytes to read from the file.
                        Default is 1MB (1024*1024 bytes).
                        For large files, you can increase this for better accuracy,
                        or decrease it for faster processing.
                        Examples: 512*1024 (512KB), 2*1024*1024 (2MB)

    Returns:
        AnalysisResult: Object containing encoding and newlines information

    Examples:
        >>> import charsetrs
        >>> result = charsetrs.analyse("file.txt")
        >>> print(result.encoding)
        'utf_8'
        >>> print(result.newlines)
        'LF'

        >>> # For large files, specify sample size
        >>> result = charsetrs.analyse("large_file.txt", max_sample_size=2*1024*1024)
        >>> print(result.encoding)
        'windows_1252'
    """
    rust_result = _analyse_from_path_stream_internal(str(file_path), max_sample_size)
    return AnalysisResult(encoding=rust_result.encoding, newlines=rust_result.newlines)


def normalize(file_path, output, encoding="utf-8", newlines="LF", max_sample_size=None):
    """
    Normalize a file by converting its encoding and newline style, saving to an output file.

    This function detects the source encoding and newlines, then converts the file
    to the specified target encoding and newline style.

    Args:
        file_path: Path to the input file (string or Path object)
        output: Path to the output file where normalized content will be written
        encoding: Target encoding name (e.g., 'utf-8', 'utf-16', 'latin-1'). Default: 'utf-8'
        newlines: Target newline style ('LF', 'CRLF', or 'CR'). Default: 'LF'
        max_sample_size: Optional. Maximum number of bytes to read for encoding detection.
                        Default is 1MB. Larger values improve detection accuracy.
                        Examples: 512*1024 (512KB), 2*1024*1024 (2MB)

    Raises:
        IOError: If file cannot be read or written
        ValueError: If encoding conversion fails
        LookupError: If target encoding is invalid

    Examples:
        >>> import charsetrs
        >>> charsetrs.normalize("file.txt", output="file_utf8.txt", encoding="utf-8", newlines="LF")

        >>> # Normalize to Windows-style with specific encoding
        >>> charsetrs.normalize("file.txt", output="file_win.txt", encoding="windows-1252", newlines="CRLF")

        >>> # For large files with custom sample size
        >>> charsetrs.normalize("large.txt", output="large_utf8.txt",
        ...                      encoding="utf-8", newlines="LF", max_sample_size=2*1024*1024)
    """
    # Detect the source encoding
    result = analyse(file_path, max_sample_size)
    source_encoding = result.encoding

    # Normalize encoding names for Python codec
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

    # Normalize source encoding
    source_normalized = source_encoding.lower().replace("-", "_")
    python_source_encoding = encoding_map.get(source_normalized, source_encoding)

    # Normalize target encoding
    target_normalized = encoding.lower().replace("-", "_")
    python_target_encoding = encoding_map.get(target_normalized, encoding)

    # Map newline styles to Python newline parameter
    newline_map = {
        "LF": "\n",
        "CRLF": "\r\n",
        "CR": "\r",
    }

    if newlines not in newline_map:
        raise ValueError(f"Invalid newlines value '{newlines}'. Must be 'LF', 'CRLF', or 'CR'")

    target_newline = newline_map[newlines]

    try:
        # Read the entire file with detected encoding in binary mode to preserve newlines
        with open(file_path, "rb") as f:
            raw_content = f.read()

        # Decode with source encoding
        content = raw_content.decode(python_source_encoding)

        # Normalize newlines to target style
        # First normalize all to \n, then convert to target
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        if newlines != "LF":
            content = content.replace("\n", target_newline)

        # Write to output file with target encoding in binary mode to preserve our newlines
        with open(output, "wb") as f:
            f.write(content.encode(python_target_encoding))

    except (UnicodeDecodeError, UnicodeEncodeError, LookupError) as e:
        raise ValueError(f"Cannot normalize file from '{source_encoding}' to '{encoding}': {str(e)}") from e
    except OSError as e:
        raise OSError(f"Cannot read or write file: {str(e)}") from e
