"""
Tests for the charsetrs API: analyse() and normalize()
"""

import os
import tempfile
from pathlib import Path

import pytest

import charsetrs


class TestAnalyseAPI:
    """Test the charsetrs.analyse() function"""

    def test_analyse_utf8_file(self):
        """Test analysing UTF-8 encoded file with LF newlines"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Hello World!\nThis is UTF-8 text\n")
            temp_path = f.name

        try:
            result = charsetrs.analyse(temp_path)
            assert result is not None
            assert isinstance(result, charsetrs.AnalysisResult)
            assert result.encoding.upper() in [
                "UTF-8",
                "UTF8",
                "UTF_8",
            ], f"Expected UTF-8, got {result.encoding}"
            assert result.newlines == "LF"
        finally:
            os.unlink(temp_path)

    def test_analyse_latin1_file(self):
        """Test analysing Latin-1 encoded file"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Olá Mundo! Texto em português: ação, não, São Paulo\n"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            result = charsetrs.analyse(temp_path)
            assert result is not None
            assert isinstance(result, charsetrs.AnalysisResult)
            # Should analyse Latin-1 or Windows-1252 (which is compatible)
            assert result.encoding.lower().replace("-", "_") in [
                "iso_8859_1",
                "windows_1252",
                "latin_1",
                "cp1252",
            ], f"Expected Latin-1 compatible, got {result.encoding}"
            assert result.newlines in ["LF", "CRLF", "CR"]
        finally:
            os.unlink(temp_path)

    def test_analyse_crlf_newlines(self):
        """Test analysing file with CRLF newlines"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Line 1\r\nLine 2\r\nLine 3\r\n")
            temp_path = f.name

        try:
            result = charsetrs.analyse(temp_path)
            assert result.newlines == "CRLF"
        finally:
            os.unlink(temp_path)

    def test_analyse_cr_newlines(self):
        """Test analysing file with CR newlines"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Line 1\rLine 2\rLine 3\r")
            temp_path = f.name

        try:
            result = charsetrs.analyse(temp_path)
            assert result.newlines == "CR"
        finally:
            os.unlink(temp_path)

    def test_analyse_with_max_sample_size(self):
        """Test analyse() with custom max_sample_size parameter"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            # Create a file with repetitive content
            test_content = "Sample text\n" * 1000
            f.write(test_content.encode("utf-8"))
            temp_path = f.name

        try:
            # Test with small sample size (512 bytes)
            result_small = charsetrs.analyse(temp_path, max_sample_size=512)
            assert result_small is not None

            # Test with larger sample size (2MB)
            result_large = charsetrs.analyse(temp_path, max_sample_size=2 * 1024 * 1024)
            assert result_large is not None

            # Both should analyse UTF-8
            assert "UTF" in result_small.encoding.upper() or "8" in result_small.encoding
            assert "UTF" in result_large.encoding.upper() or "8" in result_large.encoding
        finally:
            os.unlink(temp_path)

    def test_analyse_nonexistent_file(self):
        """Test that analyse() raises error for nonexistent file"""
        with pytest.raises(Exception):
            charsetrs.analyse("/nonexistent/path/to/file.txt")

    def test_analyse_empty_file(self):
        """Test analysing empty file raises appropriate error"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            # Empty files should raise an error
            with pytest.raises(Exception):
                charsetrs.analyse(temp_path)
        finally:
            os.unlink(temp_path)

    def test_analyse_with_path_object(self):
        """Test that analyse() works with Path objects"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Test content\n")
            temp_path = Path(f.name)

        try:
            result = charsetrs.analyse(temp_path)
            assert result is not None
            assert isinstance(result, charsetrs.AnalysisResult)
        finally:
            os.unlink(temp_path)


class TestNormalizeAPI:
    """Test the charsetrs.normalize() function"""

    def test_normalize_utf8_to_utf8_lf_to_lf(self):
        """Test normalizing UTF-8 file with LF to UTF-8 with LF (identity)"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = b"Hello World\nLine 2\nLine 3\n"
            f.write(test_content)
            temp_path = f.name

        try:
            output_path = temp_path + "_output.txt"
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="LF")

            # Verify output
            with open(output_path, "rb") as f:
                output_content = f.read()

            assert output_content == test_content
            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_lf_to_crlf(self):
        """Test normalizing LF newlines to CRLF"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Line 1\nLine 2\nLine 3\n")
            temp_path = f.name

        try:
            output_path = temp_path + "_crlf.txt"
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="CRLF")

            with open(output_path, "rb") as f:
                content = f.read()

            # Should have CRLF
            assert b"\r\n" in content
            assert content.count(b"\r\n") == 3
            assert content == b"Line 1\r\nLine 2\r\nLine 3\r\n"

            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_lf_to_cr(self):
        """Test normalizing LF newlines to CR"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Line 1\nLine 2\nLine 3\n")
            temp_path = f.name

        try:
            output_path = temp_path + "_cr.txt"
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="CR")

            with open(output_path, "rb") as f:
                content = f.read()

            # Should have CR but not CRLF
            assert b"\r" in content
            assert b"\r\n" not in content
            assert content.count(b"\r") == 3
            assert content == b"Line 1\rLine 2\rLine 3\r"

            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_crlf_to_lf(self):
        """Test normalizing CRLF newlines to LF"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Line 1\r\nLine 2\r\nLine 3\r\n")
            temp_path = f.name

        try:
            output_path = temp_path + "_lf.txt"
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="LF")

            with open(output_path, "rb") as f:
                content = f.read()

            # Should have LF but not CR
            assert b"\n" in content
            assert b"\r" not in content
            assert content == b"Line 1\nLine 2\nLine 3\n"

            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_latin1_to_utf8(self):
        """Test normalizing Latin-1 file to UTF-8"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Latin-1 text: café, São Paulo\n"
            f.write(test_content.encode("latin-1"))
            temp_path = f.name

        try:
            output_path = temp_path + "_utf8.txt"
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="LF")

            # Read output as UTF-8
            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            assert "café" in content
            assert "São Paulo" in content

            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_with_max_sample_size(self):
        """Test normalize() with custom max_sample_size parameter"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            test_content = "Sample content\n" * 500
            f.write(test_content.encode("utf-8"))
            temp_path = f.name

        try:
            output_path = temp_path + "_norm.txt"
            # Normalize with small sample size for detection
            charsetrs.normalize(
                temp_path,
                output=output_path,
                encoding="utf-8",
                newlines="LF",
                max_sample_size=512,
            )

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            assert "Sample content" in content
            os.unlink(output_path)
        finally:
            os.unlink(temp_path)

    def test_normalize_invalid_newlines(self):
        """Test that normalize() raises error for invalid newlines value"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"test\n")
            temp_path = f.name

        try:
            output_path = temp_path + "_out.txt"
            with pytest.raises(ValueError) as exc_info:
                charsetrs.normalize(temp_path, output=output_path, newlines="INVALID")
            assert "newlines" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_normalize_nonexistent_file(self):
        """Test that normalize() raises error for nonexistent file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_file:
            output_path = output_file.name

        try:
            with pytest.raises(Exception):
                charsetrs.normalize(
                    "/nonexistent/path/to/file.txt",
                    output=output_path,
                    encoding="utf-8",
                    newlines="LF",
                )
        finally:
            # Clean up in case file was created
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_normalize_with_path_object(self):
        """Test that normalize() works with Path objects"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            f.write(b"Test content\n")
            temp_path = Path(f.name)

        try:
            output_path = Path(str(temp_path) + "_out.txt")
            charsetrs.normalize(temp_path, output=output_path, encoding="utf-8", newlines="LF")

            assert output_path.exists()
            os.unlink(output_path)
        finally:
            os.unlink(temp_path)


class TestAnalyseWithTestData:
    """Test analyse() with actual test data files"""

    def test_analyse_sample_files(self):
        """Test analysis on sample data files"""
        data_dir = Path(__file__).parent / "data"

        if not data_dir.exists():
            pytest.skip("Test data directory not found")

        sample_files = list(data_dir.glob("*.txt"))

        if not sample_files:
            pytest.skip("No sample files found in test data directory")

        # Test at least one file
        for sample_file in sample_files[:5]:  # Test first 5 files
            result = charsetrs.analyse(sample_file)
            assert result is not None
            assert isinstance(result, charsetrs.AnalysisResult)
            assert len(result.encoding) > 0
            assert result.newlines in ["LF", "CRLF", "CR"]

            # Verify we can normalize the file
            output_file = str(sample_file) + "_normalized.txt"
            try:
                charsetrs.normalize(sample_file, output=output_file, encoding="utf-8", newlines="LF")
                assert os.path.exists(output_file)
                assert os.path.getsize(output_file) > 0
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
