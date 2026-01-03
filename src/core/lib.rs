use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use std::collections::HashMap;
use std::fs::File;
use std::io::Read;
use std::path::Path;

// Language detection based on Unicode ranges and character frequency
fn detect_language(text: &str, encoding: &str) -> String {
    if text.is_empty() {
        return "Unknown".to_string();
    }

    // Simple language detection based on character ranges
    let mut char_counts: HashMap<&str, usize> = HashMap::new();

    for ch in text.chars() {
        let code_point = ch as u32;

        match code_point {
            0x0600..=0x06FF | 0x0750..=0x077F | 0x08A0..=0x08FF | 0xFB50..=0xFDFF | 0xFE70..=0xFEFF => {
                *char_counts.entry("Arabic").or_insert(0) += 1;
            },
            0x0590..=0x05FF | 0xFB1D..=0xFB4F => {
                *char_counts.entry("Hebrew").or_insert(0) += 1;
            },
            0x0370..=0x03FF | 0x1F00..=0x1FFF => {
                *char_counts.entry("Greek").or_insert(0) += 1;
            },
            0x0400..=0x04FF | 0x0500..=0x052F => {
                *char_counts.entry("Cyrillic").or_insert(0) += 1;
            },
            0x4E00..=0x9FFF | 0x3400..=0x4DBF => {
                *char_counts.entry("Chinese").or_insert(0) += 1;
            },
            0x3040..=0x309F | 0x30A0..=0x30FF => {
                *char_counts.entry("Japanese").or_insert(0) += 1;
            },
            0xAC00..=0xD7AF | 0x1100..=0x11FF | 0x3130..=0x318F => {
                *char_counts.entry("Korean").or_insert(0) += 1;
            },
            0x0E00..=0x0E7F => {
                *char_counts.entry("Thai").or_insert(0) += 1;
            },
            _ => {
                if ch.is_ascii_alphabetic() || (0x00C0..=0x024F).contains(&code_point) {
                    *char_counts.entry("Latin").or_insert(0) += 1;
                }
            }
        }
    }

    // Check for non-Latin scripts first
    if let Some((&lang, &count)) = char_counts.iter().filter(|(k, _)| **k != "Latin").max_by_key(|(_, &c)| c) {
        if count > 10 {
            return match lang {
                "Cyrillic" => {
                    // Distinguish between Cyrillic languages
                    let encoding_lower = encoding.to_lowercase();
                    if text.contains("ъ") || text.contains("ѝ") || encoding_lower.contains("bulgarian") {
                        "Bulgarian".to_string()
                    } else {
                        "Russian".to_string()
                    }
                },
                other => other.to_string(),
            };
        }
    }

    // For Latin-based languages, use encoding and text patterns
    let encoding_lower = encoding.to_lowercase();
    let text_lower = text.to_lowercase();

    // Encoding-based detection
    let lang_from_encoding = match encoding_lower.as_str() {
        e if e.contains("1256") || e.contains("864") => Some("Arabic"),
        e if e.contains("1255") || e.contains("862") || e.contains("424") => Some("Hebrew"),
        e if e.contains("1253") || e.contains("737") || e.contains("greek") => Some("Greek"),
        e if e.contains("1251") || e.contains("866") || e.contains("855") || e.contains("cyrillic") || e.contains("koi") => Some("Russian"),
        e if e.contains("950") || e.contains("big5") || e.contains("gb") => Some("Chinese"),
        e if e.contains("932") || e.contains("shift") || e.contains("euc_jp") || e.contains("iso2022_jp") => Some("Japanese"),
        e if e.contains("949") || e.contains("johab") || e.contains("euc_kr") => Some("Korean"),
        e if e.contains("1254") || e.contains("857") => Some("Turkish"),
        e if e.contains("1250") || e.contains("iso_8859_2") => Some("Polish"),
        _ => None,
    };

    if let Some(lang) = lang_from_encoding {
        return lang.to_string();
    }

    // Content-based detection for Latin scripts
    // Look for language-specific patterns
    if text_lower.contains("ş") || text_lower.contains("ğ") || text_lower.contains("ı") {
        return "Turkish".to_string();
    }

    if text_lower.contains("ą") || text_lower.contains("ć") || text_lower.contains("ę") ||
       text_lower.contains("ł") || text_lower.contains("ń") || text_lower.contains("ó") ||
       text_lower.contains("ś") || text_lower.contains("ź") || text_lower.contains("ż") {
        return "Polish".to_string();
    }

    if text_lower.contains("à") || text_lower.contains("â") || text_lower.contains("ç") ||
       text_lower.contains("é") || text_lower.contains("è") || text_lower.contains("ê") ||
       text_lower.contains("ë") || text_lower.contains("î") || text_lower.contains("ï") ||
       text_lower.contains("ô") || text_lower.contains("ù") || text_lower.contains("û") ||
       text_lower.contains("ü") || text_lower.contains("ÿ") {
        // Could be French, but check for common French words
        if text_lower.contains(" le ") || text_lower.contains(" la ") || text_lower.contains(" les ") ||
           text_lower.contains(" de ") || text_lower.contains(" et ") || text_lower.contains(" des ") ||
           text_lower.contains(" du ") {
            return "French".to_string();
        }
    }

    if text_lower.contains("¿") || text_lower.contains("¡") ||
       text_lower.contains("ñ") {
        return "Spanish".to_string();
    }

    // Default to English for Latin scripts
    "English".to_string()
}

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
    #[pyo3(get)]
    language: String,
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
    let detected_language = detect_language(&best_text, &normalized_encoding);

    Ok(CharsetMatch {
        encoding: normalized_encoding,
        language: detected_language,
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
