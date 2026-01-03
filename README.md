# charset-normalizer-python-rs

A Python library with Rust bindings for detecting and reading files with different character encodings.

## Features

- Fast encoding detection using Rust
- Support for multiple encodings (UTF-8, Latin-1, Windows-1252, UTF-16, ASCII, etc.)
- Simple Python API
- Integration tests with files in different encodings

## Installation

### Development Installation

```bash
# Install maturin for building Rust extensions
pip install maturin

# Build and install in development mode
maturin develop
```

### Production Build

```bash
maturin build --release
```

## Usage

```python
from charset_normalizer_rs import detect_encoding, read_file_with_encoding

# Detect the encoding of a file
encoding = detect_encoding("path/to/file.txt")
print(f"Detected encoding: {encoding}")

# Read a file with a specific encoding
content = read_file_with_encoding("path/to/file.txt", encoding)
print(content)
```

## Testing

Run the integration tests:

```bash
pytest tests/
```

## Project Structure

```
.
├── src/              # Rust source code
│   └── lib.rs        # Main Rust library with encoding detection
├── python/           # Python package
│   └── charset_normalizer_rs/
│       └── __init__.py
├── tests/            # Integration tests
│   └── test_integration.py
├── pyproject.toml    # Python project configuration
└── Cargo.toml        # Rust project configuration
```

## License

MIT