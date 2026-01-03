from __future__ import annotations

from pathlib import Path

import pytest

DIR_PATH = Path(__file__).parent.absolute() / "data"


@pytest.mark.parametrize(
    "input_data_file, expected_charset, expected_language",
    [
        ("sample-arabic-1.txt", "cp1256", "Arabic"),
        ("sample-french-1.txt", "cp1252", "French"),
        ("sample-arabic.txt", "utf_8", "Arabic"),
        ("sample-russian-3.txt", "utf_8", "Russian"),
        ("sample-french.txt", "utf_8", "French"),
        ("sample-chinese.txt", "big5", "Chinese"),
        ("sample-greek.txt", "cp1253", "Greek"),
        ("sample-greek-2.txt", "cp1253", "Greek"),
        ("sample-hebrew-2.txt", "cp1255", "Hebrew"),
        ("sample-hebrew-3.txt", "cp1255", "Hebrew"),
        ("sample-bulgarian.txt", "utf_8", "Bulgarian"),
        ("sample-english.bom.txt", "utf_8", "English"),
        ("sample-spanish.txt", "utf_8", "Spanish"),
        ("sample-korean.txt", "cp949", "Korean"),
        ("sample-turkish.txt", "cp1254", "Turkish"),
        ("sample-russian-2.txt", "utf_8", "Russian"),
        ("sample-russian.txt", "mac_cyrillic", "Russian"),
        ("sample-polish.txt", "utf_8", "Polish"),
    ],
)
def test_elementary_detection(
    input_data_file: str,
    expected_charset: str,
    expected_language: str,
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
    assert best_guess.language == expected_language, (
        f"Elementary language detection has failed upon '{input_data_file}'. "
        f"Expected {expected_language}, got {best_guess.language}"
    )
