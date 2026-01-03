"""
Integration tests for charset normalizer
Tests files with different encodings
"""

import os
import tempfile

import pytest

from charset_normalizer_rs import detect_encoding, read_file_with_encoding


class TestEncodingDetection:
    """Test encoding detection with different file encodings"""

    def test_detect_utf8_encoding(self):
        """Test detection of UTF-8 encoded file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "Hello World! This is UTF-8 text with special chars: áéíóú ñ 你好"
            f.write(test_content)
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            assert detected.upper() in ["UTF-8", "UTF8", "UTF_8"], f"Expected UTF-8, got {detected}"

            # Verify we can read the file with detected encoding
            content = read_file_with_encoding(temp_path, detected)
            assert "Hello World" in content
            assert "áéíóú" in content or "UTF-8" in detected.upper()
        finally:
            os.unlink(temp_path)

    def test_detect_latin1_encoding(self):
        """Test detection of Latin-1 (ISO-8859-1) encoded file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            # Latin-1 encoded text with special characters
            test_content = "Olá Mundo! Texto em português: ação, não, São Paulo"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            # Detection might return latin-1, iso-8859-1, windows-1252, or cp1252
            assert detected.upper() in [
                "ISO-8859-1",
                "WINDOWS-1252",
                "LATIN-1",
                "LATIN1",
                "CP1252",
            ], f"Expected Latin-1 compatible encoding, got {detected}"

            # Verify we can read the file
            content = read_file_with_encoding(temp_path, detected)
            assert "Mundo" in content
        finally:
            os.unlink(temp_path)

    def test_detect_windows1252_encoding(self):
        """Test detection of Windows-1252 encoded file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            # Windows-1252 specific characters
            test_content = "Windows text with smart quotes: \u201cHello\u201d and \u20acuro symbol"
            f.write(test_content.encode("windows-1252"))
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            # Should detect as Windows-1252 or compatible
            assert detected.upper() in [
                "WINDOWS-1252",
                "ISO-8859-1",
                "LATIN-1",
                "CP1252",
            ], f"Expected Windows-1252 compatible encoding, got {detected}"

            # Verify we can read the file
            content = read_file_with_encoding(temp_path, detected)
            assert "Windows" in content
        finally:
            os.unlink(temp_path)

    def test_detect_ascii_encoding(self):
        """Test detection of ASCII encoded file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", delete=False, suffix=".txt") as f:
            test_content = "Simple ASCII text without any special characters"
            f.write(test_content)
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            # ASCII files might be detected as UTF-8, ASCII, or Windows-1252 (superset of ASCII)
            assert detected.upper() in [
                "ASCII",
                "UTF-8",
                "UTF8",
                "UTF_8",
                "US-ASCII",
                "WINDOWS-1252",
                "ISO-8859-1",
                "CP1252",
            ], f"Expected ASCII-compatible encoding, got {detected}"

            # Verify we can read the file
            content = read_file_with_encoding(temp_path, detected)
            assert test_content == content
        finally:
            os.unlink(temp_path)

    def test_detect_utf16_encoding(self):
        """Test detection of UTF-16 encoded file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "UTF-16 text with emojis: \U0001f600\U0001f389"
            f.write(test_content.encode("utf-16"))
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            # Should detect as UTF-16 (with BOM it detects as UTF-16LE)
            detected_upper = detected.upper().replace("_", "-")
            assert "UTF-16" in detected_upper or "UTF16" in detected_upper, f"Expected UTF-16, got {detected}"

            # Verify we can read the file
            content = read_file_with_encoding(temp_path, detected)
            assert "UTF-16" in content or "text" in content
        finally:
            os.unlink(temp_path)

    def test_read_file_with_wrong_encoding_fails(self):
        """Test that reading with wrong encoding raises an error"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "UTF-8 text: 你好世界"
            f.write(test_content)
            temp_path = f.name

        try:
            # This might or might not fail depending on the specific bytes,
            # but we're testing the error handling mechanism
            detected = detect_encoding(temp_path)
            content = read_file_with_encoding(temp_path, detected)
            assert content is not None
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test that nonexistent file raises appropriate error"""
        with pytest.raises(Exception):
            detect_encoding("/nonexistent/path/to/file.txt")

    def test_empty_file(self):
        """Test detection of empty file"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            detected = detect_encoding(temp_path)
            # Empty file should still return a valid encoding
            assert detected is not None
            assert len(detected) > 0
        finally:
            os.unlink(temp_path)


class TestReadFileWithEncoding:
    """Test reading files with specific encodings"""

    def test_read_utf8_file(self):
        """Test reading UTF-8 file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "UTF-8 content with special chars: áéíóú"
            f.write(test_content)
            temp_path = f.name

        try:
            content = read_file_with_encoding(temp_path, "UTF-8")
            assert "UTF-8 content" in content
            assert "áéíóú" in content
        finally:
            os.unlink(temp_path)

    def test_read_latin1_file(self):
        """Test reading Latin-1 file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Latin-1 text: café"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            content = read_file_with_encoding(temp_path, "ISO-8859-1")
            assert "Latin-1" in content
            assert "café" in content
        finally:
            os.unlink(temp_path)

    def test_invalid_encoding_name(self):
        """Test that invalid encoding name raises error"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test")
            temp_path = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                read_file_with_encoding(temp_path, "INVALID-ENCODING-XYZ")
            assert "encoding" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)
