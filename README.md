# charsetrs

A fast Python library with Rust bindings for detecting and converting file character encodings.

## Features

- **Simple API**: Just two functions - `detect()` and `convert()`
- **Fast encoding detection** using Rust
- **Memory efficient**: Works with large files using streaming
- **Supports multiple encodings**: UTF-8, Latin-1, Windows-1252, UTF-16, ASCII, Arabic, Korean, and more
- **Configurable sample size**: Control memory usage vs accuracy trade-off

## Installation

### Development Installation

```bash
# Install dependencies
uv sync

# Build and install in development mode
uv run maturin develop
```

### Production Build

```bash
uv run maturin build --release
```

## Usage

### Basic Usage

```python
import charsetrs

# Detect file encoding
encoding = charsetrs.detect("file.txt")
print(f"Detected encoding: {encoding}")

# Convert file to UTF-8
content = charsetrs.convert("file.txt", to="utf-8")
print(content)
```

### Working with Large Files

For large files, you can control how many bytes are read for encoding detection:

```python
import charsetrs

# Use only 512KB for detection (faster, less memory)
encoding = charsetrs.detect("large_file.txt", max_sample_size=512*1024)

# Use 2MB for detection (more accurate)
encoding = charsetrs.detect("large_file.txt", max_sample_size=2*1024*1024)

# Convert large file with custom sample size
content = charsetrs.convert("large_file.txt", to="utf-8", max_sample_size=1024*1024)
```

### Supported Encodings

- UTF-8, UTF-16 (LE/BE), UTF-32
- ISO-8859-1 (Latin-1)
- Windows code pages: 1252, 1256 (Arabic), 1255 (Hebrew), 1253 (Greek), 1251 (Cyrillic), 1254 (Turkish), 1250 (Central European)
- CP949 (Korean), EUC-KR
- Shift_JIS, EUC-JP (Japanese)
- Big5, GBK, GB2312 (Chinese)
- KOI8-R, KOI8-U (Cyrillic)
- Mac encodings (Roman, Cyrillic)
- ASCII

## API Reference

### `charsetrs.detect(file_path, max_sample_size=None)`

Detect the encoding of a file.

**Parameters:**
- `file_path` (str or Path): Path to the file
- `max_sample_size` (int, optional): Maximum bytes to read for detection (default: 1MB)

**Returns:**
- `str`: The detected encoding name (e.g., 'utf_8', 'cp1252', 'windows_1256')

### `charsetrs.convert(file_path, to, max_sample_size=None)`

Convert a file from its detected encoding to a target encoding.

**Parameters:**
- `file_path` (str or Path): Path to the file
- `to` (str): Target encoding (e.g., 'utf-8', 'latin-1')
- `max_sample_size` (int, optional): Maximum bytes to read for detection (default: 1MB)

**Returns:**
- `str`: The file content converted to the target encoding

**Raises:**
- `ValueError`: If encoding conversion fails
- `IOError`: If file cannot be read
- `LookupError`: If target encoding is invalid

## Testing

Run the test suite:

```bash
uv run pytest tests/
```

Run specific tests:

```bash
# Test new API
uv run pytest tests/test_charsetrs_api.py -v

# Test with sample files
uv run pytest tests/test_full_detection.py -v
```

## Project Structure

```
.
├── src/
│   ├── charsetrs/         # Python package
│   │   └── __init__.py    # Python API
│   └── core/              # Rust source code
│       └── lib.rs         # Rust encoding detection
├── tests/                 # Test suite
│   ├── test_charsetrs_api.py
│   ├── test_full_detection.py
│   └── data/              # Sample files in various encodings
├── pyproject.toml         # Python project configuration
└── Cargo.toml             # Rust project configuration
```

## Performance

The library uses streaming to efficiently handle large files:
- **Default**: Reads 1MB sample for detection
- **Configurable**: Adjust `max_sample_size` based on your needs
- **Memory efficient**: Suitable for multi-GB files

## License

MIT