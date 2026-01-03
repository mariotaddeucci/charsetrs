"""
Charsetrs - A Python library with Rust bindings for charset detection
"""

from charsetrs._internal import CharsetMatch
from charsetrs._internal import from_path_stream as _from_path_stream_internal

__all__ = [
    "detect",
    "convert",
    "CharsetMatch",
]
__version__ = "0.1.0"


def detect(file_path, max_sample_size=None):
    """
    Detect the encoding of a file.
    
    This function uses streaming to analyze files efficiently, making it suitable
    for large files. By default, it reads up to 1MB of the file for detection.
    
    Args:
        file_path: Path to the file to detect encoding (string or Path object)
        max_sample_size: Optional. Maximum number of bytes to read from the file.
                        Default is 1MB (1024*1024 bytes).
                        For large files, you can increase this for better accuracy,
                        or decrease it for faster processing.
                        Examples: 512*1024 (512KB), 2*1024*1024 (2MB)
    
    Returns:
        str: The detected encoding name (e.g., 'utf_8', 'cp1252', 'windows_1256')
    
    Examples:
        >>> import charsetrs
        >>> encoding = charsetrs.detect("file.txt")
        >>> print(encoding)
        'utf_8'
        
        >>> # For large files, specify sample size
        >>> encoding = charsetrs.detect("large_file.txt", max_sample_size=2*1024*1024)
        >>> print(encoding)
        'windows_1252'
    """
    match = _from_path_stream_internal(str(file_path), max_sample_size)
    return match.encoding


def convert(file_path, to, max_sample_size=None):
    """
    Convert a file from its detected encoding to a target encoding.
    
    This function detects the source encoding and converts the file content
    to the specified target encoding. For large files, you can control how
    many bytes are used for encoding detection.
    
    Args:
        file_path: Path to the file to convert (string or Path object)
        to: Target encoding name (e.g., 'utf-8', 'utf-16', 'latin-1')
        max_sample_size: Optional. Maximum number of bytes to read for encoding detection.
                        Default is 1MB. Larger values improve detection accuracy
                        for files with mixed content or rare characters.
                        Examples: 512*1024 (512KB), 2*1024*1024 (2MB)
    
    Returns:
        str: The file content converted to the target encoding
    
    Raises:
        IOError: If file cannot be read
        ValueError: If encoding conversion fails
        LookupError: If target encoding is invalid
    
    Examples:
        >>> import charsetrs
        >>> content = charsetrs.convert("file.txt", to="utf-8")
        >>> print(content)
        'Hello World...'
        
        >>> # For large files with custom sample size
        >>> content = charsetrs.convert("large_file.txt", to="utf-8", max_sample_size=512*1024)
    """
    # Detect the source encoding
    match = _from_path_stream_internal(str(file_path), max_sample_size)
    source_encoding = match.encoding
    
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
    target_normalized = to.lower().replace("-", "_")
    python_target_encoding = encoding_map.get(target_normalized, to)
    
    try:
        # Read the entire file with detected encoding
        with open(file_path, encoding=python_source_encoding, errors="strict") as f:
            content = f.read()
        
        # Encode to target encoding and decode back to string to validate
        content.encode(python_target_encoding)
        
        return content
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError) as e:
        raise ValueError(
            f"Cannot convert file from '{source_encoding}' to '{to}': {str(e)}"
        ) from e
