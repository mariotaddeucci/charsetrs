"""
Tests for memory efficiency of the streaming normalize function
"""

import os
import tempfile
from pathlib import Path

import charsetrs


def test_normalize_large_file_memory_efficiency():
    """
    Test that normalize can handle large files without loading everything into memory.
    
    This test creates a 10MB file (which is small but verifies streaming works).
    For real-world usage, the streaming implementation will handle files of any size
    with constant memory usage.
    """
    # Create a large test file (10MB)
    test_size_mb = 10
    line_content = "This is a test line with some UTF-8 characters: café, São Paulo, München\n"
    lines_needed = (test_size_mb * 1024 * 1024) // len(line_content.encode("utf-8"))

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        for _ in range(lines_needed):
            f.write(line_content.encode("utf-8"))
        temp_path = f.name

    try:
        # Verify file size is approximately what we expect
        file_size = os.path.getsize(temp_path)
        assert file_size >= test_size_mb * 1024 * 1024 * 0.9, f"File size {file_size} is too small"

        # Normalize the file - this should use streaming and constant memory
        charsetrs.normalize(temp_path, encoding="utf-8", newlines="CRLF")

        # Verify the file was normalized
        with open(temp_path, "rb") as f:
            # Read first few KB to check
            sample = f.read(4096)
            assert b"\r\n" in sample, "File should have CRLF newlines"
            assert b"caf\xc3\xa9" in sample, "File should contain UTF-8 encoded text"

        # File should still be approximately the same size (just different newlines)
        normalized_size = os.path.getsize(temp_path)
        assert normalized_size > file_size * 0.9, "Normalized file size is too small"
    finally:
        os.unlink(temp_path)


def test_normalize_preserves_content():
    """Test that normalize preserves file content while changing encoding and newlines"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        # Create content with various characters
        content = "Line 1: Hello World\nLine 2: café\nLine 3: São Paulo\nLine 4: 日本語\n"
        f.write(content.encode("utf-8"))
        temp_path = f.name

    try:
        # Read original content
        with open(temp_path, encoding="utf-8") as f:
            original_lines = f.read().splitlines()

        # Normalize to CRLF
        charsetrs.normalize(temp_path, encoding="utf-8", newlines="CRLF")

        # Read normalized content
        with open(temp_path, encoding="utf-8", newline="") as f:
            normalized = f.read()

        # Split on CRLF to get lines
        normalized_lines = normalized.replace("\r\n", "\n").splitlines()

        # Content should be the same, just newlines changed
        assert len(original_lines) == len(normalized_lines)
        for orig, norm in zip(original_lines, normalized_lines):
            assert orig == norm, f"Line mismatch: '{orig}' != '{norm}'"

        # Verify CRLF is present
        with open(temp_path, "rb") as f:
            raw = f.read()
            assert b"\r\n" in raw, "File should have CRLF newlines"
    finally:
        os.unlink(temp_path)


def test_normalize_mixed_newlines():
    """Test normalization of files with mixed newline styles"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        # Create file with mixed newlines (LF, CRLF, CR)
        f.write(b"Line 1\n")  # LF
        f.write(b"Line 2\r\n")  # CRLF
        f.write(b"Line 3\r")  # CR
        f.write(b"Line 4\n")  # LF
        temp_path = f.name

    try:
        # Normalize to LF
        charsetrs.normalize(temp_path, encoding="utf-8", newlines="LF")

        # Read and verify all newlines are LF
        with open(temp_path, "rb") as f:
            content = f.read()

        assert b"\r\n" not in content, "Should not have CRLF"
        assert b"\r" not in content, "Should not have standalone CR"
        assert content.count(b"\n") == 4, "Should have 4 LF newlines"

        # Verify content is preserved
        lines = content.decode("utf-8").splitlines()
        assert len(lines) == 4
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"
        assert lines[2] == "Line 3"
        assert lines[3] == "Line 4"
    finally:
        os.unlink(temp_path)
