from __future__ import annotations

from pathlib import Path

import pytest

DIR_PATH = Path(__file__).parent.absolute() / "data"


@pytest.mark.parametrize(
    "input_data_file, expected_charset",
    [
        ("sample-arabic-1.txt", "cp1256"),
        ("sample-french-1.txt", "cp1252"),
        ("sample-arabic.txt", "utf_8"),
        ("sample-russian-3.txt", "utf_8"),
        ("sample-french.txt", "utf_8"),
        ("sample-chinese.txt", "big5"),
        ("sample-greek.txt", "cp1253"),
        ("sample-greek-2.txt", "cp1253"),
        ("sample-hebrew-2.txt", "cp1255"),
        ("sample-hebrew-3.txt", "cp1255"),
        ("sample-bulgarian.txt", "utf_8"),
        ("sample-english.bom.txt", "utf_8"),
        ("sample-spanish.txt", "utf_8"),
        ("sample-korean.txt", "cp949"),
        ("sample-turkish.txt", "cp1254"),
        ("sample-russian-2.txt", "utf_8"),
        ("sample-russian.txt", "mac_cyrillic"),
        ("sample-polish.txt", "utf_8"),
    ],
)
def test_elementary_detection(
    input_data_file: str,
    expected_charset: str,
):
    from charset_normalizer_rs import from_path

    file_path = DIR_PATH / input_data_file
    best_guess = from_path(file_path).best()

    assert best_guess is not None, (
        f"Elementary detection has failed upon '{input_data_file}'"
    )
    assert best_guess.encoding == expected_charset, (
        f"Elementary charset detection has failed upon '{input_data_file}'. "
        f"Expected {expected_charset}, got {best_guess.encoding}"
    )
