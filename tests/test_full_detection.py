from pathlib import Path

import pytest
from charset_normalizer import from_path as cn_from_path

import charsetrs

DIR_PATH = Path(__file__).parent.absolute() / "data"


@pytest.mark.parametrize("file_path", [p.absolute() for p in DIR_PATH.glob("*")])
def test_elementary_detection(
    file_path: Path,
):
    expected = cn_from_path(file_path.as_posix())
    expected_best = expected.best()
    if expected_best is None:
        pytest.skip(f"No charset detected by charset_normalizer for {file_path}")
    expected_charset = expected_best.encoding

    detected_charset = charsetrs.detect(file_path.as_posix())

    assert detected_charset == expected_charset, (  # noqa: S101
        f"Expected charset {expected_charset}, got {detected_charset} for file {file_path}"
    )
