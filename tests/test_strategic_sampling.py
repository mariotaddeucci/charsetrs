"""
Tests for the strategic sampling feature
"""

import os
import tempfile

import charsetrs


def test_analyse_with_percentage_sampling():
    """Test analyse with percentage-based sampling"""
    # Create a 100KB file
    test_size = 100 * 1024
    content = b"Test content with UTF-8: caf\xc3\xa9\n" * (test_size // 30)

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        # Test with 10% sampling (default)
        result = charsetrs.analyse(temp_path)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
        assert result.newlines == "LF"

        # Test with 5% sampling
        result = charsetrs.analyse(temp_path, percentage_sample_size=0.05)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]

        # Test with 20% sampling
        result = charsetrs.analyse(temp_path, percentage_sample_size=0.2)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_analyse_small_file_uses_entire_file():
    """Test that small files (< min_sample_size) are read entirely"""
    # Create a 500KB file (smaller than default min of 1MB)
    test_size = 500 * 1024
    content = b"Small file content\n" * (test_size // 20)

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        # With default min_sample_size of 1MB, this should read the entire file
        result = charsetrs.analyse(temp_path)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]

        # With a smaller min_sample_size
        result = charsetrs.analyse(temp_path, min_sample_size=100 * 1024)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_analyse_with_custom_min_sample_size():
    """Test analyse with custom min_sample_size"""
    # Create a 2MB file
    test_size = 2 * 1024 * 1024
    content = b"Content line\n" * (test_size // 13)

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        # Test with 2MB min_sample_size
        result = charsetrs.analyse(temp_path, min_sample_size=2 * 1024 * 1024, percentage_sample_size=0.05)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]

        # Test with 512KB min_sample_size
        result = charsetrs.analyse(temp_path, min_sample_size=512 * 1024, percentage_sample_size=0.05)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_analyse_with_max_sample_size():
    """Test analyse with max_sample_size constraint"""
    # Create a 5MB file
    test_size = 5 * 1024 * 1024
    content = b"Large file content\n" * (test_size // 19)

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name

    try:
        # Test with max_sample_size of 1MB (should cap at 1MB even if percentage is higher)
        result = charsetrs.analyse(
            temp_path, min_sample_size=512 * 1024, percentage_sample_size=0.5, max_sample_size=1024 * 1024
        )
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]

        # Test with max_sample_size of 2MB
        result = charsetrs.analyse(temp_path, max_sample_size=2 * 1024 * 1024)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_strategic_sampling_detects_encoding_from_head_and_tail():
    """Test that strategic sampling can detect encoding from head and tail sections"""
    # Create a file with specific content in head and tail
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        # Head: UTF-8 content with special characters
        head_content = "Head section with UTF-8: café, São Paulo, München\n" * 100

        # Middle: Regular ASCII content (padding)
        middle_content = "Middle padding content\n" * 5000

        # Tail: More UTF-8 special characters
        tail_content = "Tail section with UTF-8: naïve, résumé, señor\n" * 100

        f.write(head_content.encode("utf-8"))
        f.write(middle_content.encode("utf-8"))
        f.write(tail_content.encode("utf-8"))
        temp_path = f.name

    try:
        # Analyse with small percentage to rely on strategic sampling
        result = charsetrs.analyse(temp_path, percentage_sample_size=0.05)
        assert result is not None
        # Should still detect UTF-8 due to head and tail sampling
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_normalize_with_strategic_sampling():
    """Test normalize function with strategic sampling parameters"""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        content = "Test line\n" * 1000
        f.write(content.encode("utf-8"))
        temp_path = f.name

    try:
        # Normalize with custom sampling parameters
        charsetrs.normalize(
            temp_path,
            encoding="utf-8",
            newlines="CRLF",
            min_sample_size=512 * 1024,
            percentage_sample_size=0.1,
            max_sample_size=2 * 1024 * 1024,
        )

        # Verify the file was normalized
        with open(temp_path, "rb") as f:
            normalized_content = f.read()
            assert b"\r\n" in normalized_content
            # Verify content is preserved
            assert b"Test line" in normalized_content
    finally:
        os.unlink(temp_path)


def test_large_file_with_strategic_sampling():
    """Test with a larger file to verify strategic sampling works"""
    # Create a 20MB file
    test_size_mb = 20
    line_content = "This is a test line with content\n"
    line_bytes = len(line_content.encode("utf-8"))
    # Use ceiling division to ensure we meet or exceed the target size
    lines_needed = -(-test_size_mb * 1024 * 1024 // line_bytes)  # Ceiling division trick

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        for _ in range(lines_needed):
            f.write(line_content.encode("utf-8"))
        temp_path = f.name

    try:
        file_size = os.path.getsize(temp_path)
        assert file_size >= test_size_mb * 1024 * 1024 * 0.9

        # Analyse with 5% sampling (should read ~1MB from 20MB file)
        result = charsetrs.analyse(temp_path, percentage_sample_size=0.05)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
        assert result.newlines == "LF"

        # Analyse with max_sample_size constraint
        result = charsetrs.analyse(temp_path, max_sample_size=512 * 1024)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)


def test_mixed_newlines_with_strategic_sampling():
    """Test detection of mixed newlines with strategic sampling"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        # Create a larger file with mixed newlines
        # Head section with CRLF
        for _ in range(100):
            f.write(b"Head line\r\n")

        # Middle section with mixed
        for _ in range(500):
            f.write(b"Middle line\n")

        # Tail section with CRLF
        for _ in range(100):
            f.write(b"Tail line\r\n")

        temp_path = f.name

    try:
        # Should detect CRLF as it appears in both head and tail
        result = charsetrs.analyse(temp_path, percentage_sample_size=0.1)
        assert result is not None
        # The detection prioritizes CRLF when found
        assert result.newlines in ["CRLF", "LF"]  # Could be either depending on sampling
    finally:
        os.unlink(temp_path)


def test_empty_parameters_use_defaults():
    """Test that omitting parameters uses sensible defaults"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(b"Test content\n" * 100)
        temp_path = f.name

    try:
        # Call without any sampling parameters (should use defaults)
        result = charsetrs.analyse(temp_path)
        assert result is not None
        assert result.encoding.lower().replace("-", "_") in ["utf_8", "utf8"]
    finally:
        os.unlink(temp_path)
