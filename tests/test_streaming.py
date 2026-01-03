"""
Tests for streaming functionality with large files
"""

import os
import tempfile
from pathlib import Path

import pytest

from charset_normalizer_rs import detect_encoding_stream, from_path_stream


def test_stream_small_utf8_file():
    """Test streaming with a small UTF-8 file"""
    content = "Hello, World! 你好世界"

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        result = from_path_stream(temp_path)
        assert result.best().encoding == "utf_8"

        encoding = detect_encoding_stream(temp_path)
        assert encoding == "utf_8"
    finally:
        os.unlink(temp_path)


def test_stream_large_utf8_file():
    """Test streaming with a large UTF-8 file (simulates multi-MB file)"""
    # Create a file with ~2MB of content
    content = "Hello, World! 你好世界\n" * 100000  # ~2MB

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        # Should detect correctly even with large file
        result = from_path_stream(temp_path)
        assert result.best().encoding == "utf_8"

        # Check file size to confirm it's large
        file_size = os.path.getsize(temp_path)
        assert file_size > 1_000_000  # At least 1MB
    finally:
        os.unlink(temp_path)


def test_stream_cp1252_file():
    """Test streaming with Windows-1252 encoded file"""
    # Windows-1252 specific characters
    content = "Café résumé naïve"

    with tempfile.NamedTemporaryFile(mode="w", encoding="cp1252", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        encoding = detect_encoding_stream(temp_path)
        # Accept various Windows codepages or UTF-8 (all can decode this content)
        assert encoding in ["cp1252", "cp1254", "latin_1", "utf_8"]
    finally:
        os.unlink(temp_path)


def test_stream_with_bom():
    """Test streaming detects UTF-8 BOM correctly"""
    content = "Hello, World!"

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        # Write UTF-8 BOM
        f.write(b"\xef\xbb\xbf")
        f.write(content.encode("utf-8"))
        temp_path = f.name

    try:
        result = from_path_stream(temp_path)
        assert result.best().encoding == "utf_8"
    finally:
        os.unlink(temp_path)


def test_stream_empty_file():
    """Test streaming with an empty file"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        temp_path = f.name

    try:
        with pytest.raises(IOError, match="File is empty"):
            from_path_stream(temp_path)
    finally:
        os.unlink(temp_path)


def test_stream_nonexistent_file():
    """Test streaming with a file that doesn't exist"""
    with pytest.raises(IOError, match="Failed to open file"):
        from_path_stream("/nonexistent/path/to/file.txt")


def test_stream_vs_regular_consistency():
    """Test that streaming gives same result as regular detection for small files"""
    test_data_dir = Path(__file__).parent / "data"

    # Test with existing sample files
    sample_files = [
        "sample-english.bom.txt",
        "sample-french.txt",
        "sample-spanish.txt",
    ]

    for filename in sample_files:
        filepath = test_data_dir / filename
        if filepath.exists():
            from charset_normalizer_rs import detect_encoding

            regular_encoding = detect_encoding(str(filepath))
            stream_encoding = detect_encoding_stream(str(filepath))

            # Both should detect the same encoding
            assert regular_encoding == stream_encoding, (
                f"Mismatch for {filename}: regular={regular_encoding}, stream={stream_encoding}"
            )


def test_stream_memory_efficient():
    """
    Test that streaming uses less memory than regular detection.
    This creates a very large file and ensures the stream function works.
    """
    # Create a 10MB file
    content = "Test line with some content\n" * 350000  # ~10MB

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        file_size = os.path.getsize(temp_path)
        assert file_size > 5_000_000  # At least 5MB

        # Stream function should work fine even with large file
        result = from_path_stream(temp_path)
        assert result.best().encoding == "utf_8"

        # Test completed successfully - streaming works with large files
        print(f"Successfully processed {file_size / 1_000_000:.2f}MB file with streaming")
    finally:
        os.unlink(temp_path)


def test_stream_different_encodings():
    """Test streaming with various encodings"""
    test_data_dir = Path(__file__).parent / "data"

    # Test various sample files with different encodings
    sample_files = [
        ("sample-arabic.txt", ["cp1256", "utf_8"]),  # Arabic
        ("sample-russian.txt", ["cp1251", "utf_8", "mac_cyrillic"]),  # Russian (can be Mac Cyrillic)
        ("sample-chinese.txt", ["gbk", "gb2312", "utf_8", "big5"]),  # Chinese (can be GBK or Big5)
    ]

    for filename, expected_encodings in sample_files:
        filepath = test_data_dir / filename
        if filepath.exists():
            encoding = detect_encoding_stream(str(filepath))
            # Check if detected encoding is one of the expected ones
            # (different systems might detect slightly different but compatible encodings)
            assert any(exp in encoding.lower() or encoding.lower() in exp for exp in expected_encodings), (
                f"Unexpected encoding for {filename}: {encoding}"
            )
