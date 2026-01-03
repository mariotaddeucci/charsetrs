"""
Tests for the new charsetrs API: detect() and convert()
"""

import os
import tempfile
from pathlib import Path

import pytest

import charsetrs


class TestDetectAPI:
    """Test the charsetrs.detect() function"""

    def test_detect_utf8_file(self):
        """Test detecting UTF-8 encoded file"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "Hello World! This is UTF-8 text with special chars: áéíóú ñ 你好"
            f.write(test_content)
            temp_path = f.name

        try:
            encoding = charsetrs.detect(temp_path)
            assert encoding is not None
            assert isinstance(encoding, str)
            # UTF-8 detection
            assert encoding.upper() in ["UTF-8", "UTF8", "UTF_8"], f"Expected UTF-8, got {encoding}"
        finally:
            os.unlink(temp_path)

    def test_detect_latin1_file(self):
        """Test detecting Latin-1 encoded file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Olá Mundo! Texto em português: ação, não, São Paulo"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            encoding = charsetrs.detect(temp_path)
            assert encoding is not None
            assert isinstance(encoding, str)
            # Should detect Latin-1 or Windows-1252 (which is compatible)
            assert encoding.lower().replace("-", "_") in [
                "iso_8859_1",
                "windows_1252",
                "latin_1",
                "cp1252",
            ], f"Expected Latin-1 compatible, got {encoding}"
        finally:
            os.unlink(temp_path)

    def test_detect_with_max_sample_size(self):
        """Test detect() with custom max_sample_size parameter"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            # Create a file with repetitive content
            test_content = "Sample text " * 1000 + " with special chars: áéíóú"
            f.write(test_content)
            temp_path = f.name

        try:
            # Test with small sample size (512 bytes)
            encoding_small = charsetrs.detect(temp_path, max_sample_size=512)
            assert encoding_small is not None
            
            # Test with larger sample size (2MB)
            encoding_large = charsetrs.detect(temp_path, max_sample_size=2 * 1024 * 1024)
            assert encoding_large is not None
            
            # Both should detect UTF-8
            assert "UTF" in encoding_small.upper() or "8" in encoding_small
            assert "UTF" in encoding_large.upper() or "8" in encoding_large
        finally:
            os.unlink(temp_path)

    def test_detect_nonexistent_file(self):
        """Test that detect() raises error for nonexistent file"""
        with pytest.raises(Exception):
            charsetrs.detect("/nonexistent/path/to/file.txt")

    def test_detect_empty_file(self):
        """Test detecting empty file raises appropriate error"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            # Empty files should raise an error
            with pytest.raises(Exception):
                charsetrs.detect(temp_path)
        finally:
            os.unlink(temp_path)

    def test_detect_with_path_object(self):
        """Test that detect() works with Path objects"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            encoding = charsetrs.detect(temp_path)
            assert encoding is not None
            assert isinstance(encoding, str)
        finally:
            os.unlink(temp_path)


class TestConvertAPI:
    """Test the charsetrs.convert() function"""

    def test_convert_utf8_to_utf8(self):
        """Test converting UTF-8 file to UTF-8 (identity conversion)"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "Hello World with UTF-8 chars: áéíóú ñ"
            f.write(test_content)
            temp_path = f.name

        try:
            content = charsetrs.convert(temp_path, to="utf-8")
            assert content is not None
            assert isinstance(content, str)
            assert "Hello World" in content
            assert "áéíóú" in content
        finally:
            os.unlink(temp_path)

    def test_convert_latin1_to_utf8(self):
        """Test converting Latin-1 file to UTF-8"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Latin-1 text: café, naïve, São Paulo"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            content = charsetrs.convert(temp_path, to="utf-8")
            assert content is not None
            assert isinstance(content, str)
            assert "café" in content
            assert "São Paulo" in content
        finally:
            os.unlink(temp_path)

    def test_convert_with_max_sample_size(self):
        """Test convert() with custom max_sample_size parameter"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            test_content = "Sample content " * 500 + " special: áéíóú"
            f.write(test_content)
            temp_path = f.name

        try:
            # Convert with small sample size for detection
            content = charsetrs.convert(temp_path, to="utf-8", max_sample_size=512)
            assert content is not None
            assert "Sample content" in content
            assert "special: áéíóú" in content
        finally:
            os.unlink(temp_path)

    def test_convert_utf8_to_latin1(self):
        """Test converting UTF-8 to Latin-1 (lossy for some chars)"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            # Use only Latin-1 compatible characters
            test_content = "Simple Latin text: café"
            f.write(test_content)
            temp_path = f.name

        try:
            content = charsetrs.convert(temp_path, to="latin-1")
            assert content is not None
            assert "café" in content
        finally:
            os.unlink(temp_path)

    def test_convert_invalid_target_encoding(self):
        """Test that convert() raises error for invalid target encoding"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                charsetrs.convert(temp_path, to="INVALID-ENCODING-XYZ")
            error_msg = str(exc_info.value).lower()
            assert "encoding" in error_msg or "convert" in error_msg
        finally:
            os.unlink(temp_path)

    def test_convert_nonexistent_file(self):
        """Test that convert() raises error for nonexistent file"""
        with pytest.raises(Exception):
            charsetrs.convert("/nonexistent/path/to/file.txt", to="utf-8")

    def test_convert_with_path_object(self):
        """Test that convert() works with Path objects"""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
            f.write("Test content with UTF-8: áéíóú")
            temp_path = Path(f.name)

        try:
            content = charsetrs.convert(temp_path, to="utf-8")
            assert content is not None
            assert "Test content" in content
        finally:
            os.unlink(temp_path)


class TestDetectWithTestData:
    """Test detect() with actual test data files"""

    def test_detect_sample_files(self):
        """Test detection on sample data files"""
        data_dir = Path(__file__).parent / "data"
        
        if not data_dir.exists():
            pytest.skip("Test data directory not found")
        
        sample_files = list(data_dir.glob("*.txt"))
        
        if not sample_files:
            pytest.skip("No sample files found in test data directory")
        
        # Test at least one file
        for sample_file in sample_files[:5]:  # Test first 5 files
            encoding = charsetrs.detect(sample_file)
            assert encoding is not None
            assert isinstance(encoding, str)
            assert len(encoding) > 0
            
            # Verify we can convert the file
            content = charsetrs.convert(sample_file, to="utf-8")
            assert content is not None
            assert len(content) > 0
