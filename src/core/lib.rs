use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use std::fs::File;
use std::io::Read;
use std::path::Path;

// Normalize encoding name to Python codec format
fn normalize_encoding_name(encoding: &str) -> String {
    let normalized = encoding.to_lowercase().replace("-", "_");

    match normalized.as_str() {
        "utf_8" | "utf8" => "utf_8".to_string(),
        "iso_8859_1" | "iso8859_1" | "latin_1" | "latin1" => "latin_1".to_string(),
        "windows_1252" | "cp_1252" => "cp1252".to_string(),
        "windows_1256" | "cp_1256" => "cp1256".to_string(),
        "windows_1255" | "cp_1255" => "cp1255".to_string(),
        "windows_1253" | "cp_1253" => "cp1253".to_string(),
        "windows_1251" | "cp_1251" => "cp1251".to_string(),
        "windows_1254" | "cp_1254" => "cp1254".to_string(),
        "windows_1250" | "cp_1250" => "cp1250".to_string(),
        "windows_949" | "cp_949" => "cp949".to_string(),
        "shift_jis" | "shift_jis_2004" => "shift_jis".to_string(),
        "euc_jp" | "euc-jp" => "euc_jp".to_string(),
        "euc_kr" | "euc-kr" => "euc_kr".to_string(),
        "gb2312" | "gb_2312" => "gb2312".to_string(),
        "gbk" => "gbk".to_string(),
        "big5" => "big5".to_string(),
        "macintosh" | "mac_roman" => "mac_roman".to_string(),
        "mac_cyrillic" | "x_mac_cyrillic" => "mac_cyrillic".to_string(),
        "koi8_r" | "koi8r" => "koi8_r".to_string(),
        "koi8_u" => "koi8_u".to_string(),
        other if other.starts_with("cp_") => other.replace("_", ""),
        other => other.to_string(),
    }
}

/// CharsetMatch represents a single encoding detection result
#[pyclass]
#[derive(Clone)]
struct CharsetMatch {
    #[pyo3(get)]
    encoding: String,
    raw_bytes: Vec<u8>,
    decoded_text: String,
}

#[pymethods]
impl CharsetMatch {
    fn __str__(&self) -> PyResult<String> {
        Ok(self.decoded_text.clone())
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("<CharsetMatch '{}' bytes ({})>", self.encoding, self.raw_bytes.len()))
    }
}

/// Detects encoding and language from a file
#[pyfunction]
fn from_path(file_path: String) -> PyResult<CharsetMatch> {
    // Read the file as bytes
    let path = Path::new(&file_path);
    let mut file = File::open(path).map_err(|e| {
        PyIOError::new_err(format!("Failed to open file: {}", e))
    })?;

    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).map_err(|e| {
        PyIOError::new_err(format!("Failed to read file: {}", e))
    })?;

    // Check for BOM markers
    let (encoding_str, skip_bytes) = if buffer.starts_with(&[0xEF, 0xBB, 0xBF]) {
        ("utf_8", 3)
    } else if buffer.starts_with(&[0xFF, 0xFE]) {
        ("utf_16_le", 2)
    } else if buffer.starts_with(&[0xFE, 0xFF]) {
        ("utf_16_be", 2)
    } else {
        // Use chardet for initial detection
        let result = chardet::detect(&buffer);
        let detected = result.0.to_lowercase().replace("-", "_");

        // Map chardet output to proper encoding names
        let encoding = match detected.as_str() {
            "utf_8" | "utf8" | "ascii" => "UTF-8",
            "big5" | "big_5" => "Big5",
            "gb2312" | "gb_2312" | "gbk" => "GBK",
            "windows_1252" | "cp1252" | "iso_8859_1" => "windows-1252",
            "windows_1256" | "cp1256" | "iso_8859_6" => "windows-1256",
            "windows_1255" | "cp1255" | "iso_8859_8" => "windows-1255",
            "windows_1253" | "cp1253" | "iso_8859_7" => "windows-1253",
            "windows_1251" | "cp1251" | "iso_8859_5" => "windows-1251",
            "windows_1254" | "cp1254" | "iso_8859_9" => "windows-1254",
            "windows_1250" | "cp1250" | "iso_8859_2" => "windows-1250",
            "euc_kr" | "cp949" | "windows_949" | "ks_c_5601_1987" => "windows-949",
            "shift_jis" | "shift_jisx0213" | "cp932" => "shift_jis",
            "euc_jp" => "EUC-JP",
            "mac_cyrillic" | "x_mac_cyrillic" => "x-mac-cyrillic",
            "koi8_r" | "koi8r" => "KOI8-R",
            _ => "UTF-8", // fallback
        };
        (encoding, 0)
    };

    // Try to decode with detected encoding
    let buffer_slice = &buffer[skip_bytes..];

    // List of encodings to try
    let encodings_to_try = vec![
        encoding_str,
        "UTF-8",
        "windows-1252",
        "windows-1256",
        "windows-1255",
        "windows-1253",
        "windows-1251",
        "windows-1254",
        "windows-1250",
        "windows-949",
        "Big5",
        "GBK",
        "shift_jis",
        "EUC-JP",
        "EUC-KR",
        "x-mac-cyrillic",
        "ISO-8859-1",
    ];

    let mut best_encoding = None;
    let mut best_text = String::new();
    let mut min_error_ratio = 1.0;

    for encoding_name in &encodings_to_try {
        if let Some(encoding) = encoding_rs::Encoding::for_label(encoding_name.as_bytes()) {
            let (decoded, _, had_errors) = encoding.decode(buffer_slice);

            // Calculate error ratio
            let error_chars = decoded.chars().filter(|&c| c == '\u{FFFD}').count();
            let total_chars = decoded.chars().count().max(1);
            let error_ratio = error_chars as f32 / total_chars as f32;

            if !had_errors || error_ratio < min_error_ratio {
                min_error_ratio = error_ratio;
                best_encoding = Some(encoding.name().to_string());
                best_text = decoded.to_string();

                // If perfect decode, stop searching
                if !had_errors && error_ratio == 0.0 {
                    break;
                }
            }
        }
    }

    let final_encoding = best_encoding.unwrap_or_else(|| "UTF-8".to_string());
    let normalized_encoding = normalize_encoding_name(&final_encoding);

    Ok(CharsetMatch {
        encoding: normalized_encoding,
        raw_bytes: buffer,
        decoded_text: best_text,
    })
}

/// A Python module implemented in Rust.
#[pymodule]
fn _internal(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(from_path, m)?)?;
    m.add_class::<CharsetMatch>()?;
    Ok(())
}
