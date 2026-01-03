"""
Charset Normalizer RS - A Python library with Rust bindings for charset detection
"""

from charset_normalizer_rs._internal import detect_encoding, read_file_with_encoding

__all__ = ["detect_encoding", "read_file_with_encoding"]
__version__ = "0.1.0"
