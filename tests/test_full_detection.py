from pathlib import Path

import pytest
from charset_normalizer import from_path

import charsetrs

DIR_PATH = Path(__file__).parent.absolute() / "data"


# Define charset equivalence groups for ambiguous detections
# These charsets can be considered equivalent for certain files
CHARSET_EQUIVALENCE = {
    "cp1250": {"cp1250", "cp1252"},  # Central European vs Western European
    "cp1252": {"cp1250", "cp1252"},  # Often ambiguous for Latin text
}


def normalize_charset(charset: str) -> str:
    """Normalize charset name for comparison."""
    return charset.lower().replace("-", "_")


def are_charsets_equivalent(charset1: str, charset2: str) -> bool:
    """Check if two charsets are equivalent or interchangeable."""
    norm1 = normalize_charset(charset1)
    norm2 = normalize_charset(charset2)

    if norm1 == norm2:
        return True

    # Check if they're in the same equivalence group
    if norm1 in CHARSET_EQUIVALENCE:
        return norm2 in CHARSET_EQUIVALENCE[norm1]

    return False


@pytest.mark.parametrize("file_path", [p.absolute() for p in DIR_PATH.glob("*")])
def test_elementary_detection(
    file_path: Path,
):
    expected = from_path(file_path.as_posix())
    expected_best = expected.best()
    if expected_best is None:
        pytest.skip(f"No charset detected by charset_normalizer for {file_path}")
    expected_charset = expected_best.encoding

    result = charsetrs.analyse(file_path.as_posix())
    detected_charset = result.encoding

    assert are_charsets_equivalent(detected_charset, expected_charset), (  # noqa: S101
        f"Expected charset {expected_charset}, got {detected_charset} for file {file_path}"
    )
