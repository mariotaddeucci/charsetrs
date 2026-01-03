# charsetrs

A fast Python library with Rust bindings for detecting file character encodings and normalizing files.

## Features

- **Simple API**: Just two functions - `analyse()` and `normalize()`
- **Fast encoding detection** using Rust
- **Newline detection**: Detects LF, CRLF, or CR newline styles
- **File normalization**: Convert encoding and newlines in one step
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

# Analyse file encoding and newline style
result = charsetrs.analyse("file.txt")
print(f"Encoding: {result.encoding}")  # e.g., 'utf_8'
print(f"Newlines: {result.newlines}")  # e.g., 'LF', 'CRLF', or 'CR'

# Normalize file to UTF-8 with LF newlines
charsetrs.normalize(
    "file.txt",
    output="file_utf8.txt",
    encoding="utf-8",
    newlines="LF"
)
```

### Working with Large Files

For large files, you can control how many bytes are read for encoding detection:

```python
import charsetrs

# Use only 512KB for detection (faster, less memory)
result = charsetrs.analyse("large_file.txt", max_sample_size=512*1024)

# Use 2MB for detection (more accurate)
result = charsetrs.analyse("large_file.txt", max_sample_size=2*1024*1024)

# Normalize large file with custom sample size
charsetrs.normalize(
    "large_file.txt",
    output="large_utf8.txt",
    encoding="utf-8",
    newlines="LF",
    max_sample_size=1024*1024
)
```

### Newline Normalization

Convert between different newline styles:

```python
import charsetrs

# Convert Windows-style (CRLF) to Unix-style (LF)
charsetrs.normalize("windows.txt", output="unix.txt", encoding="utf-8", newlines="LF")

# Convert to Windows-style (CRLF)
charsetrs.normalize("unix.txt", output="windows.txt", encoding="utf-8", newlines="CRLF")

# Convert to old Mac-style (CR)
charsetrs.normalize("file.txt", output="mac.txt", encoding="utf-8", newlines="CR")
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

### `charsetrs.analyse(file_path, max_sample_size=None)`

Analyse the encoding and newline style of a file.

**Parameters:**
- `file_path` (str or Path): Path to the file
- `max_sample_size` (int, optional): Maximum bytes to read for detection (default: 1MB)

**Returns:**
- `AnalysisResult`: Object with `encoding` and `newlines` attributes

**Example:**
```python
result = charsetrs.analyse("file.txt")
print(result.encoding)  # 'utf_8'
print(result.newlines)  # 'LF'
```

### `charsetrs.normalize(file_path, output, encoding="utf-8", newlines="LF", max_sample_size=None)`

Normalize a file by converting its encoding and newline style.

**Parameters:**
- `file_path` (str or Path): Path to the input file
- `output` (str or Path): Path to the output file
- `encoding` (str, optional): Target encoding (default: 'utf-8')
- `newlines` (str, optional): Target newline style - 'LF', 'CRLF', or 'CR' (default: 'LF')
- `max_sample_size` (int, optional): Maximum bytes to read for detection (default: 1MB)

**Raises:**
- `ValueError`: If encoding conversion fails or invalid newlines value
- `IOError`: If file cannot be read or written
- `LookupError`: If target encoding is invalid

**Example:**
```python
charsetrs.normalize(
    "input.txt",
    output="output.txt",
    encoding="utf-8",
    newlines="LF"
)
```

### `AnalysisResult`

A frozen dataclass containing analysis results:

```python
@dataclass(frozen=True)
class AnalysisResult:
    encoding: str                        # e.g., 'utf_8', 'cp1252'
    newlines: Literal["LF", "CRLF", "CR"]  # Detected newline style
```

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