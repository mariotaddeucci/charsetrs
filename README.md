# charsetrs

A fast Python library with Rust bindings for detecting file character encodings and normalizing files.

## Features

- **Simple API**: Just two functions - `analyse()` and `normalize()`
- **Fast encoding detection** using Rust
- **Newline detection**: Detects LF, CRLF, or CR newline styles
- **File normalization**: Convert encoding and newlines in-place using streaming
- **Memory efficient**: Constant memory usage (~56KB) for files of any size
- **Supports large files**: Process 10GB+ files on 512MB RAM systems
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

# Normalize file to UTF-8 with LF newlines (in-place modification)
charsetrs.normalize(
    "file.txt",
    encoding="utf-8",
    newlines="LF"
)
```

### Working with Large Files

The library uses streaming with strategic sampling to efficiently handle files of any size with constant memory usage (~56KB):

```python
import charsetrs

# Default sampling: 10% of file with 1MB minimum
result = charsetrs.analyse("large_file.txt")

# Use only 5% of file for faster detection
result = charsetrs.analyse("large_file.txt", percentage_sample_size=0.05)

# Cap maximum sample size to 2MB
result = charsetrs.analyse("large_file.txt", max_sample_size=2*1024*1024)

# Adjust minimum sample size for better accuracy on smaller files
result = charsetrs.analyse("medium_file.txt", min_sample_size=512*1024)

# Normalize large file with custom sampling
# Memory usage: ~56KB regardless of file size (10GB+ files supported)
charsetrs.normalize(
    "large_file.txt",
    encoding="utf-8",
    newlines="LF",
    percentage_sample_size=0.05,
    max_sample_size=2*1024*1024
)
```

**Strategic Sampling:**
- Reads 35% from the beginning of the file
- Reads 15% from the end of the file
- Reads 50% distributed in chunks throughout the middle
- Never loads the entire file into memory
- Ideal for 10GB+ files on 512MB RAM systems

### Newline Normalization

Convert between different newline styles (in-place modification):

```python
import charsetrs

# Convert Windows-style (CRLF) to Unix-style (LF)
charsetrs.normalize("windows.txt", encoding="utf-8", newlines="LF")

# Convert to Windows-style (CRLF)
charsetrs.normalize("unix.txt", encoding="utf-8", newlines="CRLF")

# Convert to old Mac-style (CR)
charsetrs.normalize("file.txt", encoding="utf-8", newlines="CR")
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

### `charsetrs.analyse(file_path, min_sample_size=1024*1024, percentage_sample_size=0.1, max_sample_size=None)`

Analyse the encoding and newline style of a file using strategic sampling.

**Parameters:**
- `file_path` (str or Path): Path to the file
- `min_sample_size` (int, optional): Minimum bytes to sample. Default: 1MB (1024*1024). For files smaller than this, the entire file is sampled.
- `percentage_sample_size` (float, optional): Percentage of file to sample (0.0 to 1.0). Default: 0.1 (10% of file).
- `max_sample_size` (int, optional): Maximum bytes to sample. Default: None (no limit). Use to cap memory usage for very large files.

**Returns:**
- `AnalysisResult`: Object with `encoding` and `newlines` attributes

**Sampling Strategy:**
The function reads samples strategically from the file without loading it entirely:
- 35% from the beginning of the file
- 15% from the end of the file
- 50% distributed uniformly in chunks throughout the middle

**Example:**
```python
result = charsetrs.analyse("file.txt")
print(result.encoding)  # 'utf_8'
print(result.newlines)  # 'LF'

# Custom sampling for large files
result = charsetrs.analyse("large.txt", 
                          min_sample_size=2*1024*1024,
                          percentage_sample_size=0.05,
                          max_sample_size=10*1024*1024)
```

### `charsetrs.normalize(file_path, encoding="utf-8", newlines="LF", min_sample_size=1024*1024, percentage_sample_size=0.1, max_sample_size=None)`

Normalize a file by converting its encoding and newline style in-place using streaming.

This function modifies the file in-place with constant memory usage (~56KB), making it suitable for very large files (10GB+) on memory-constrained systems (512MB RAM).

**Parameters:**
- `file_path` (str or Path): Path to the file to normalize
- `encoding` (str, optional): Target encoding (default: 'utf-8')
- `newlines` (str, optional): Target newline style - 'LF', 'CRLF', or 'CR' (default: 'LF')
- `min_sample_size` (int, optional): Minimum bytes to sample. Default: 1MB.
- `percentage_sample_size` (float, optional): Percentage of file to sample. Default: 0.1 (10%).
- `max_sample_size` (int, optional): Maximum bytes to sample. Default: None.

**Raises:**
- `ValueError`: If encoding conversion fails or invalid newlines value
- `IOError`: If file cannot be read or written
- `LookupError`: If target encoding is invalid

**Example:**
```python
charsetrs.normalize(
    "input.txt",
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

## Development Tasks

The project uses taskipy for common development tasks:

```bash
# Run tests
uv run task test

# Format all code (Python + Rust)
uv run task format

# Check formatting and linting (Python + Rust)
uv run task lint

# Format only Rust code
uv run task format_rust

# Lint only Rust code (formatting + clippy)
uv run task lint_rust
```

## Project Structure

```
.
├── src/
│   ├── charsetrs/         # Python package
│   │   └── __init__.py    # Python API
│   └── charsetrs_core/        # Rust source code
│       └── lib.rs         # Rust encoding detection
├── tests/                 # Test suite
│   ├── test_charsetrs_api.py
│   ├── test_full_detection.py
│   └── data/              # Sample files in various encodings
├── pyproject.toml         # Python project configuration
└── Cargo.toml             # Rust project configuration
```

## Performance

The library uses streaming with strategic sampling to efficiently handle large files:
- **Constant memory usage**: ~56KB regardless of file size
- **Suitable for large files**: Process 10GB+ files on 512MB RAM systems
- **Smart sampling**: Reads from beginning (35%), end (15%), and middle (50% distributed)
- **Default detection**: Samples 10% of file with 1MB minimum
- **Configurable**: Adjust `min_sample_size`, `percentage_sample_size`, and `max_sample_size` based on your needs
- **Single-pass processing**: Linear time complexity O(n) for normalization

For more details, see [MEMORY_EFFICIENCY.md](MEMORY_EFFICIENCY.md)

## License

MIT