use pyo3::exceptions::PyIOError;
use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::Path;

// Constantes para controle de memória
const CHUNK_SIZE: usize = 8192; // 8KB por chunk
const MAX_SAMPLE_SIZE: usize = 1024 * 1024; // 1MB de amostra máxima para análise

// Normalize encoding name to Python codec format
fn normalize_encoding_name(encoding: &str) -> String {
    let normalized = encoding.to_lowercase().replace("-", "_");

    match normalized.as_str() {
        "utf_8" | "utf8" => "utf_8".to_string(),
        "utf_16" | "utf16" => "utf_16".to_string(),
        "utf_16_le" | "utf16_le" | "utf_16le" | "utf16le" => "utf_16le".to_string(),
        "utf_16_be" | "utf16_be" | "utf_16be" | "utf16be" => "utf_16be".to_string(),
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

/// AnalysisResult represents the result of file analysis with encoding and newline style
#[pyclass]
#[derive(Clone)]
struct AnalysisResult {
    #[pyo3(get)]
    encoding: String,
    #[pyo3(get)]
    newlines: String,
}

#[pymethods]
impl AnalysisResult {
    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "AnalysisResult(encoding='{}', newlines='{}')",
            self.encoding, self.newlines
        ))
    }
}

// Detect newline style from buffer
fn detect_newline_style(buffer: &[u8]) -> &'static str {
    let mut has_crlf = false;
    let mut has_lf_only = false;
    let mut has_cr_only = false;

    let mut i = 0;
    while i < buffer.len() {
        if buffer[i] == b'\r' {
            if i + 1 < buffer.len() && buffer[i + 1] == b'\n' {
                has_crlf = true;
                i += 2;
            } else {
                has_cr_only = true;
                i += 1;
            }
        } else if buffer[i] == b'\n' {
            has_lf_only = true;
            i += 1;
        } else {
            i += 1;
        }
    }

    // Prioritize CRLF if found (Windows style)
    if has_crlf {
        "CRLF"
    } else if has_lf_only {
        "LF"
    } else if has_cr_only {
        "CR"
    } else {
        // Default to LF if no newlines found
        "LF"
    }
}

// Analyze byte patterns to detect likely encoding type
fn analyze_byte_patterns(buffer: &[u8]) -> Vec<&'static str> {
    let mut hints = Vec::new();

    // Count byte ranges
    let high_bytes = buffer.iter().filter(|&&b| b >= 0x80).count();
    if high_bytes == 0 {
        return hints; // Pure ASCII
    }

    let total_len = buffer.len() as f32;

    // Byte distribution analysis
    let lower_high = buffer.iter().filter(|&&b| b >= 0xC0 && b < 0xE0).count();
    let upper_high = buffer.iter().filter(|&&b| b >= 0xE0).count();
    let arabic_specific = buffer.iter().filter(|&&b| b >= 0xC0 && b <= 0xE5).count();

    let lower_ratio = lower_high as f32 / total_len;
    let upper_ratio = upper_high as f32 / total_len;
    let arabic_ratio = arabic_specific as f32 / total_len;

    // Turkish specific bytes
    let turkish_specific = buffer
        .iter()
        .filter(|&&b| matches!(b, 0xF0 | 0xFD | 0xFE))
        .count();

    // Mac Cyrillic has very high concentration (>60%) in upper range (0xE0-0xFF)
    // while Arabic spreads more evenly
    if upper_ratio > 0.55 && lower_ratio < 0.35 {
        hints.push("likely_mac_cyrillic");
    }
    // Arabic has good spread in 0xC0-0xE5 but not too much upper concentration
    else if arabic_ratio > 0.35 && upper_ratio < 0.65 {
        hints.push("likely_arabic");
    }

    if turkish_specific >= 2 {
        hints.push("likely_turkish");
    }

    hints
}

// Detect UTF-16 by analyzing null byte patterns
fn detect_utf16_pattern(buffer: &[u8]) -> Option<&'static str> {
    if buffer.len() < 20 {
        return None;
    }

    // Count null bytes in even and odd positions
    let sample_size = buffer.len().min(1000);
    let even_nulls = buffer[..sample_size]
        .iter()
        .step_by(2)
        .filter(|&&b| b == 0)
        .count();
    let odd_nulls = buffer[..sample_size]
        .iter()
        .skip(1)
        .step_by(2)
        .filter(|&&b| b == 0)
        .count();

    let threshold = sample_size / 16; // ~6% threshold

    // UTF-16-LE has nulls in odd positions (for ASCII range)
    if odd_nulls > threshold && even_nulls < threshold / 2 {
        return Some("UTF-16LE");
    }
    // UTF-16-BE has nulls in even positions (for ASCII range)
    if even_nulls > threshold && odd_nulls < threshold / 2 {
        return Some("UTF-16BE");
    }

    None
}

// Detect language characteristics from decoded text
fn detect_language_hints(text: &str) -> Vec<&'static str> {
    let mut hints = Vec::new();

    let total_chars = text.chars().count().max(1);

    let arabic_chars = text
        .chars()
        .filter(|c| {
            let code = *c as u32;
            // Arabic block + Arabic Presentation Forms
            (code >= 0x0600 && code <= 0x06FF)
                || (code >= 0xFB50 && code <= 0xFDFF)
                || (code >= 0xFE70 && code <= 0xFEFF)
        })
        .count();

    let cyrillic_chars = text
        .chars()
        .filter(|c| {
            let code = *c as u32;
            (code >= 0x0400 && code <= 0x04FF) || (code >= 0x0500 && code <= 0x052F)
        })
        .count();

    let turkish_specific = text
        .chars()
        .filter(|c| {
            // Turkish-specific letters that don't appear in other Latin scripts
            matches!(*c, 'ğ' | 'Ğ' | 'ı' | 'İ' | 'ş' | 'Ş')
        })
        .count();

    let korean_chars = text
        .chars()
        .filter(|c| {
            let code = *c as u32;
            // Hangul Syllables + Hangul Jamo
            (code >= 0xAC00 && code <= 0xD7AF)
                || (code >= 0x1100 && code <= 0x11FF)
                || (code >= 0x3130 && code <= 0x318F)
        })
        .count();

    // Calculate percentages
    let arabic_ratio = arabic_chars as f32 / total_chars as f32;
    let cyrillic_ratio = cyrillic_chars as f32 / total_chars as f32;
    let korean_ratio = korean_chars as f32 / total_chars as f32;

    // Arabic text typically has high ratio of Arabic characters
    if arabic_ratio > 0.3 {
        hints.push("arabic");
    }
    // Cyrillic, but not if there's more Arabic
    if cyrillic_ratio > 0.2 && arabic_ratio < 0.1 {
        hints.push("cyrillic");
    }
    // Turkish needs at least a few specific chars
    if turkish_specific >= 3 {
        hints.push("turkish");
    }
    // Korean text has very high ratio of Korean chars
    if korean_ratio > 0.2 {
        hints.push("korean");
    }

    hints
}

/// Analyzes encoding and newline style from a file using streaming
#[pyfunction]
#[pyo3(signature = (file_path, max_sample_size=None))]
fn analyse_from_path_stream(
    file_path: String,
    max_sample_size: Option<usize>,
) -> PyResult<AnalysisResult> {
    let path = Path::new(&file_path);
    let file =
        File::open(path).map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;

    let max_size = max_sample_size.unwrap_or(MAX_SAMPLE_SIZE);

    let mut reader = BufReader::new(file);
    let mut buffer = Vec::new();
    let mut total_read = 0;

    // Read file in chunks
    loop {
        let mut chunk = vec![0u8; CHUNK_SIZE];
        let bytes_read = reader
            .read(&mut chunk)
            .map_err(|e| PyIOError::new_err(format!("Failed to read file: {}", e)))?;

        if bytes_read == 0 {
            break;
        }

        buffer.extend_from_slice(&chunk[..bytes_read]);
        total_read += bytes_read;

        if total_read >= max_size {
            break;
        }
    }

    if buffer.is_empty() {
        return Err(PyIOError::new_err("File is empty"));
    }

    // Detect newline style
    let newlines = detect_newline_style(&buffer);

    // Detect encoding (reuse existing logic)
    let (encoding_str, skip_bytes) = if buffer.starts_with(&[0xEF, 0xBB, 0xBF]) {
        ("utf_8", 3)
    } else if buffer.starts_with(&[0xFF, 0xFE]) {
        ("UTF-16LE", 2)
    } else if buffer.starts_with(&[0xFE, 0xFF]) {
        ("UTF-16BE", 2)
    } else if buffer.starts_with(&[0xFF, 0xFE, 0x00, 0x00]) {
        ("UTF-32LE", 4)
    } else if buffer.starts_with(&[0x00, 0x00, 0xFE, 0xFF]) {
        ("UTF-32BE", 4)
    } else if let Some(utf16_encoding) = detect_utf16_pattern(&buffer) {
        (utf16_encoding, 0)
    } else {
        let byte_hints = analyze_byte_patterns(&buffer);
        let result = chardet::detect(&buffer);
        let detected = result.0.to_lowercase().replace("-", "_");

        let encoding = match detected.as_str() {
            "utf_8" | "utf8" | "ascii" => "UTF-8",
            "big5" | "big_5" => "Big5",
            "gb2312" | "gb_2312" | "gbk" => "GBK",
            "windows_1252" | "cp1252" | "iso_8859_1" => {
                if byte_hints.contains(&"likely_turkish") {
                    "windows-1254"
                } else {
                    "windows-1252"
                }
            }
            "windows_1256" | "cp1256" | "iso_8859_6" => "windows-1256",
            "windows_1255" | "cp1255" | "iso_8859_8" => "windows-1255",
            "windows_1253" | "cp1253" | "iso_8859_7" => "windows-1253",
            "windows_1251" | "cp1251" | "iso_8859_5" => {
                if byte_hints.contains(&"likely_arabic") {
                    "windows-1256"
                } else if byte_hints.contains(&"likely_mac_cyrillic") {
                    "x-mac-cyrillic"
                } else {
                    "windows-1251"
                }
            }
            "windows_1254" | "cp1254" | "iso_8859_9" => "windows-1254",
            "windows_1250" | "cp1250" | "iso_8859_2" => "windows-1250",
            "euc_kr" | "cp949" | "windows_949" | "ks_c_5601_1987" => "windows-949",
            "shift_jis" | "shift_jisx0213" | "cp932" => "shift_jis",
            "euc_jp" => "EUC-JP",
            "mac_cyrillic" | "x_mac_cyrillic" => "x-mac-cyrillic",
            "koi8_r" | "koi8r" => "KOI8-R",
            _ => "UTF-8",
        };
        (encoding, 0)
    };

    let buffer_slice = &buffer[skip_bytes..];
    let mut encodings_to_try = vec![encoding_str];

    let byte_hints = analyze_byte_patterns(&buffer);

    for enc in &[
        "UTF-8",
        "x-mac-cyrillic",
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
        "mac-cyrillic",
        "KOI8-R",
        "ISO-8859-1",
    ] {
        if !encodings_to_try.contains(enc) {
            encodings_to_try.push(enc);
        }
    }

    let mut best_encoding = None;
    let mut min_error_ratio = 1.0;
    let mut best_score = f32::MIN;

    for encoding_name in &encodings_to_try {
        if let Some(encoding) = encoding_rs::Encoding::for_label(encoding_name.as_bytes()) {
            let (decoded, _, had_errors) = encoding.decode(buffer_slice);

            let error_chars = decoded.chars().filter(|&c| c == '\u{FFFD}').count();
            let total_chars = decoded.chars().count().max(1);
            let error_ratio = error_chars as f32 / total_chars as f32;

            let mut score = 1.0 - error_ratio;

            if encoding_name == &encoding_str {
                score += 0.05;
            }

            let lang_hints = detect_language_hints(&decoded);

            if lang_hints.contains(&"arabic") && encoding_name.contains("1256") {
                score += 0.5;
            }
            if lang_hints.contains(&"turkish") && encoding_name.contains("1254") {
                score += 0.4;
            }
            if lang_hints.contains(&"korean") {
                if encoding_name.contains("949") || encoding_name.contains("windows-949") {
                    score += 0.4;
                } else if encoding_name.contains("euc-kr") || encoding_name.contains("EUC-KR") {
                    score += 0.2;
                }
            }
            if lang_hints.contains(&"cyrillic") {
                if encoding_name.contains("mac-cyrillic")
                    || encoding_name.contains("x-mac-cyrillic")
                {
                    score += 0.5;
                } else if encoding_name.contains("1251") {
                    score += 0.2;
                }
            }

            if lang_hints.contains(&"arabic") && encoding_name.contains("1251") {
                score -= 0.5;
            }
            if lang_hints.contains(&"cyrillic") && encoding_name.contains("1256") {
                score -= 0.9;
            }

            if byte_hints.contains(&"likely_mac_cyrillic")
                && (encoding_name.contains("mac-cyrillic")
                    || encoding_name.contains("x-mac-cyrillic"))
            {
                score += 0.4;
            }

            if score > best_score || (score == best_score && error_ratio < min_error_ratio) {
                best_score = score;
                min_error_ratio = error_ratio;
                best_encoding = Some(encoding.name().to_string());

                if !had_errors && error_ratio == 0.0 && score > 1.0 {
                    break;
                }
            }
        }
    }

    let mut final_encoding = best_encoding.unwrap_or_else(|| "UTF-8".to_string());

    if final_encoding.to_lowercase().contains("euc-kr")
        || final_encoding.to_lowercase().contains("euc_kr")
    {
        final_encoding = "windows-949".to_string();
    }

    let normalized_encoding = normalize_encoding_name(&final_encoding);

    Ok(AnalysisResult {
        encoding: normalized_encoding,
        newlines: newlines.to_string(),
    })
}

// Helper function to get encoding_rs::Encoding from encoding name
fn get_encoding_rs(encoding_name: &str) -> Option<&'static encoding_rs::Encoding> {
    let normalized = encoding_name.to_lowercase().replace("-", "_");

    let label = match normalized.as_str() {
        "utf_8" | "utf8" => "utf-8",
        "utf_16" | "utf16" => "utf-16",
        "utf_16_le" | "utf16_le" | "utf_16le" | "utf16le" => "utf-16le",
        "utf_16_be" | "utf16_be" | "utf_16be" | "utf16be" => "utf-16be",
        "iso_8859_1" | "iso8859_1" | "latin_1" | "latin1" => "iso-8859-1",
        "windows_1252" | "cp1252" | "cp_1252" => "windows-1252",
        "windows_1256" | "cp1256" | "cp_1256" => "windows-1256",
        "windows_1255" | "cp1255" | "cp_1255" => "windows-1255",
        "windows_1253" | "cp1253" | "cp_1253" => "windows-1253",
        "windows_1251" | "cp1251" | "cp_1251" => "windows-1251",
        "windows_1254" | "cp1254" | "cp_1254" => "windows-1254",
        "windows_1250" | "cp1250" | "cp_1250" => "windows-1250",
        "windows_949" | "cp949" | "cp_949" => "windows-949",
        "shift_jis" | "shift_jisx0213" | "cp932" => "shift_jis",
        "euc_jp" | "eucjp" => "euc-jp",
        "euc_kr" | "euckr" => "euc-kr",
        "gb2312" | "gb_2312" => "gb2312",
        "gbk" => "gbk",
        "big5" => "big5",
        "mac_roman" | "macintosh" => "macintosh",
        "mac_cyrillic" | "x_mac_cyrillic" => "x-mac-cyrillic",
        "koi8_r" | "koi8r" => "koi8-r",
        "koi8_u" | "koi8u" => "koi8-u",
        other => other,
    };

    encoding_rs::Encoding::for_label(label.as_bytes())
}

/// Normalize a file by converting its encoding and newline style using streaming
///
/// This function processes files in chunks to maintain constant memory usage,
/// making it suitable for very large files (10GB+) on systems with limited RAM (512MB).
#[pyfunction]
#[pyo3(signature = (file_path, output_path, target_encoding="utf-8", target_newlines="LF", max_sample_size=None))]
fn normalize_file_stream(
    file_path: String,
    output_path: String,
    target_encoding: &str,
    target_newlines: &str,
    max_sample_size: Option<usize>,
) -> PyResult<()> {
    // Validate target_newlines
    let newline_bytes: &[u8] = match target_newlines {
        "LF" => b"\n",
        "CRLF" => b"\r\n",
        "CR" => b"\r",
        _ => {
            return Err(PyIOError::new_err(format!(
                "Invalid newlines value '{}'. Must be 'LF', 'CRLF', or 'CR'",
                target_newlines
            )))
        }
    };

    // First, analyse the file to detect source encoding
    let analysis = analyse_from_path_stream(file_path.clone(), max_sample_size)?;

    // Get source and target encodings
    let source_encoding = get_encoding_rs(&analysis.encoding).ok_or_else(|| {
        PyIOError::new_err(format!(
            "Unsupported source encoding: {}",
            analysis.encoding
        ))
    })?;

    let target_encoding_rs = get_encoding_rs(target_encoding).ok_or_else(|| {
        PyIOError::new_err(format!("Unsupported target encoding: {}", target_encoding))
    })?;

    // Open input and output files
    let input_path = Path::new(&file_path);
    let output_path_obj = Path::new(&output_path);

    let input_file = File::open(input_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open input file: {}", e)))?;
    let output_file = File::create(output_path_obj)
        .map_err(|e| PyIOError::new_err(format!("Failed to create output file: {}", e)))?;

    let mut reader = BufReader::new(input_file);
    let mut writer = BufWriter::new(output_file);

    // Create decoder and encoder
    let mut decoder = source_encoding.new_decoder();
    let mut encoder = target_encoding_rs.new_encoder();

    // Buffers for streaming processing
    let mut input_buffer = vec![0u8; CHUNK_SIZE];
    let mut decode_buffer = String::with_capacity(CHUNK_SIZE * 2);
    let mut encode_buffer = vec![0u8; CHUNK_SIZE * 4]; // Larger to accommodate multi-byte encodings

    // State for newline conversion
    let mut pending_cr = false; // Track if previous chunk ended with CR

    loop {
        // Read chunk from input
        let bytes_read = reader
            .read(&mut input_buffer)
            .map_err(|e| PyIOError::new_err(format!("Failed to read from input file: {}", e)))?;

        let is_last = bytes_read == 0;

        // Decode chunk
        decode_buffer.clear();
        let (result, _bytes_read, _had_errors) =
            decoder.decode_to_string(&input_buffer[..bytes_read], &mut decode_buffer, is_last);

        if result == encoding_rs::CoderResult::OutputFull {
            return Err(PyIOError::new_err("Decode buffer too small"));
        }

        // Process and write decoded chunk with newline conversion
        if !decode_buffer.is_empty() {
            process_and_write_chunk(
                &decode_buffer,
                &mut encoder,
                &mut encode_buffer,
                &mut writer,
                newline_bytes,
                &mut pending_cr,
                is_last,
            )?;
        }

        if is_last {
            break;
        }
    }

    // Flush the writer
    writer
        .flush()
        .map_err(|e| PyIOError::new_err(format!("Failed to flush output: {}", e)))?;

    Ok(())
}

// Helper function to process a text chunk, convert newlines, and write to output
fn process_and_write_chunk(
    text: &str,
    encoder: &mut encoding_rs::Encoder,
    encode_buffer: &mut Vec<u8>,
    writer: &mut BufWriter<File>,
    newline_bytes: &[u8],
    pending_cr: &mut bool,
    is_last: bool,
) -> PyResult<()> {
    // Process text character by character to handle newlines
    let mut output = String::with_capacity(text.len());
    let chars: Vec<char> = text.chars().collect();

    for (i, &ch) in chars.iter().enumerate() {
        if *pending_cr {
            // Previous chunk ended with CR
            if ch == '\n' {
                // This is CRLF split across chunks, output target newline
                output.push_str(std::str::from_utf8(newline_bytes).unwrap());
                *pending_cr = false;
                continue;
            } else {
                // Previous CR was standalone, output it and continue
                output.push_str(std::str::from_utf8(newline_bytes).unwrap());
                *pending_cr = false;
            }
        }

        match ch {
            '\r' => {
                // Check if next char is \n
                if i + 1 < chars.len() && chars[i + 1] == '\n' {
                    // CRLF - will handle \n in next iteration
                    output.push_str(std::str::from_utf8(newline_bytes).unwrap());
                } else if i + 1 == chars.len() && !is_last {
                    // CR at end of chunk, might be part of CRLF
                    *pending_cr = true;
                } else {
                    // Standalone CR
                    output.push_str(std::str::from_utf8(newline_bytes).unwrap());
                }
            }
            '\n' => {
                // Check if this is part of CRLF (previous char was \r)
                if i > 0 && chars[i - 1] == '\r' {
                    // Already handled as CRLF, skip
                    continue;
                } else {
                    // Standalone LF
                    output.push_str(std::str::from_utf8(newline_bytes).unwrap());
                }
            }
            _ => {
                output.push(ch);
            }
        }
    }

    // Encode and write the processed text
    if !output.is_empty() {
        let mut start = 0;
        loop {
            let (result, bytes_read, bytes_written, _had_errors) =
                encoder.encode_from_utf8(&output[start..], encode_buffer, is_last);

            // Write encoded bytes
            if bytes_written > 0 {
                writer
                    .write_all(&encode_buffer[..bytes_written])
                    .map_err(|e| PyIOError::new_err(format!("Failed to write to output: {}", e)))?;
            }

            start += bytes_read;

            if result == encoding_rs::CoderResult::InputEmpty {
                break;
            }
        }
    }

    Ok(())
}

/// A Python module implemented in Rust.
#[pymodule]
fn _internal(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyse_from_path_stream, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_file_stream, m)?)?;
    m.add_class::<AnalysisResult>()?;
    Ok(())
}
