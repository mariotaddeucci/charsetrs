"""
Charsetrs - A Python library with Rust bindings for charset detection
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from charsetrs._internal import (
    analyse_from_path_stream as _analyse_from_path_stream_internal,
)
from charsetrs._internal import (
    normalize_file_stream as _normalize_file_stream_internal,
)

try:
    from charsetrs.version import __version__  # type: ignore
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "analyse",
    "normalize",
    "AnalysisResult",
    "__version__",
]


@dataclass(frozen=True)
class AnalysisResult:
    """Result of file analysis containing encoding and newline style information."""

    encoding: str
    newlines: Literal["LF", "CRLF", "CR"]


def analyse(
    file_path: str | Path,
    min_sample_size: int = 1024 * 1024,
    percentage_sample_size: float = 0.1,
    max_sample_size: int | None = None,
) -> AnalysisResult:
    """
    Analyse the encoding and newline style of a file.

    This function uses streaming to analyze files efficiently with a smart sampling
    strategy that reads from the beginning, middle, and end of the file without
    loading the entire file into memory.

    Args:
        file_path: Path to the file to analyse (string or Path object)
        min_sample_size: Minimum number of bytes to sample. Default is 1MB.
                        For files smaller than this, the entire file is sampled.
        percentage_sample_size: Percentage of file to sample (0.0 to 1.0).
                               Default is 0.1 (10% of the file).
        max_sample_size: Optional maximum number of bytes to sample.
                        Default is None (no maximum limit).
                        Can be used to cap memory usage for very large files.

    Returns:
        AnalysisResult: Object containing encoding and newlines information

    Sampling Strategy:
        The function reads samples strategically without loading the entire file:
        - 35% from the beginning of the file
        - 15% from the end of the file
        - 50% distributed in chunks throughout the middle

    Examples:
        >>> import charsetrs
        >>> result = charsetrs.analyse("file.txt")
        >>> print(result.encoding)
        'utf_8'
        >>> print(result.newlines)
        'LF'

        >>> # For large files with custom sampling
        >>> result = charsetrs.analyse("large_file.txt",
        ...                           min_sample_size=2*1024*1024,
        ...                           percentage_sample_size=0.05,
        ...                           max_sample_size=10*1024*1024)
        >>> print(result.encoding)
        'windows_1252'
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    file_path = file_path.absolute()
    if file_path.is_dir():
        raise ValueError(f"Provided path '{file_path}' is a directory, expected a file path.")

    if file_path.exists() is False:
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    rust_result = _analyse_from_path_stream_internal(
        file_path.as_posix(), min_sample_size, percentage_sample_size, max_sample_size
    )
    return AnalysisResult(
        encoding=rust_result.encoding,
        newlines=rust_result.newlines,
    )


def _encodings_are_equivalent(source_enc: str, target_enc: str) -> bool:
    """Check if two encoding names are equivalent, considering common aliases."""
    source_normalized = source_enc.lower().replace("-", "_")
    target_normalized = target_enc.lower().replace("-", "_")

    if source_normalized == target_normalized:
        return True

    # Map common encoding aliases
    encoding_aliases = {
        "utf_8": ["utf8"],
        "utf_16": ["utf16"],
        "latin_1": ["iso_8859_1", "latin1"],
        "cp1252": ["windows_1252"],
    }

    # Check if both encodings are aliases of the same canonical encoding
    for canonical, aliases in encoding_aliases.items():
        # Include canonical name in the set of valid aliases
        all_aliases = {canonical, *aliases}
        if source_normalized in all_aliases and target_normalized in all_aliases:
            return True

    return False


def normalize(
    file_path: str | Path,
    encoding: str = "utf-8",
    newlines: Literal["LF", "CRLF", "CR"] = "LF",
    min_sample_size: int = 1024 * 1024,
    percentage_sample_size: float = 0.1,
    max_sample_size: int | None = None,
):
    """
    Normalize a file by converting its encoding and newline style in-place.

    This function uses streaming to process files efficiently, making it suitable
    for very large files (10GB+) with constant memory usage. The file is modified
    in-place using a temporary file and atomic rename.

    Args:
        file_path: Path to the input file (string or Path object)
        encoding: Target encoding name (e.g., 'utf-8', 'utf-16', 'latin-1'). Default: 'utf-8'
        newlines: Target newline style ('LF', 'CRLF', or 'CR'). Default: 'LF'
        min_sample_size: Minimum number of bytes to sample. Default is 1MB.
        percentage_sample_size: Percentage of file to sample (0.0 to 1.0). Default is 0.1 (10%).
        max_sample_size: Optional maximum number of bytes to sample. Default is None.

    Raises:
        IOError: If file cannot be read or written
        ValueError: If encoding conversion fails or invalid newlines value
        LookupError: If target encoding is invalid

    Examples:
        >>> import charsetrs
        >>> charsetrs.normalize("file.txt", encoding="utf-8", newlines="LF")

        >>> # Normalize to Windows-style with specific encoding
        >>> charsetrs.normalize("file.txt", encoding="windows-1252", newlines="CRLF")

        >>> # For large files with custom sampling
        >>> charsetrs.normalize("large.txt", encoding="utf-8", newlines="LF",
        ...                    min_sample_size=2*1024*1024,
        ...                    percentage_sample_size=0.05)
    """
    # Validate inputs
    if isinstance(file_path, str):
        file_path = Path(file_path)

    file_path = file_path.absolute()
    if file_path.is_dir():
        raise ValueError(f"Provided path '{file_path}' is a directory, expected a file path.")

    if not file_path.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    # Check if normalization is needed
    result = analyse(file_path, min_sample_size, percentage_sample_size, max_sample_size)

    # Check if encodings are equivalent and newlines match
    if _encodings_are_equivalent(result.encoding, encoding) and result.newlines == newlines:
        # No normalization needed
        return

    # Create temporary output file in the same directory for atomic rename
    temp_output = file_path.parent / f".{file_path.name}.tmp"

    try:
        # Call Rust streaming normalize function
        try:
            _normalize_file_stream_internal(
                file_path.as_posix(),
                temp_output.as_posix(),
                encoding,
                newlines,
                min_sample_size,
                percentage_sample_size,
                max_sample_size,
            )
        except OSError as e:
            # Convert OSError from Rust to ValueError for invalid newlines
            error_msg = str(e)
            if "Invalid newlines value" in error_msg:
                raise ValueError(error_msg) from e
            raise

        # Create backup of original file
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        file_path.rename(backup_path)

        try:
            # Atomically replace original with normalized version
            temp_output.rename(file_path)
            # Remove backup if successful
            backup_path.unlink()
        except Exception:
            # Restore original file if rename failed
            backup_path.rename(file_path)
            raise

    except Exception:
        # Clean up temporary file if it exists
        if temp_output.exists():
            temp_output.unlink()
        raise
