use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use std::fs::File;
use std::io::Read;
use std::path::Path;

/// Detects the encoding of a file by trying multiple encodings
/// Returns the best encoding that can successfully decode the file
#[pyfunction]
fn detect_encoding(file_path: String) -> PyResult<String> {
    // Read the file as bytes
    let path = Path::new(&file_path);
    let mut file = File::open(path).map_err(|e| {
        PyIOError::new_err(format!("Failed to open file: {}", e))
    })?;
    
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).map_err(|e| {
        PyIOError::new_err(format!("Failed to read file: {}", e))
    })?;
    
    // Try to detect encoding using chardet
    let result = chardet::detect(&buffer);
    let detected_charset = result.0;
    let confidence = result.1;
    
    // List of encodings to try in order of preference
    let encodings_to_try = vec![
        detected_charset.to_string(),
        "UTF-8".to_string(),
        "ISO-8859-1".to_string(),
        "Windows-1252".to_string(),
        "UTF-16LE".to_string(),
        "UTF-16BE".to_string(),
        "ASCII".to_string(),
    ];
    
    // Try each encoding
    for encoding_name in &encodings_to_try {
        if let Some(encoding) = encoding_rs::Encoding::for_label(encoding_name.as_bytes()) {
            let (_decoded, _, had_errors) = encoding.decode(&buffer);
            if !had_errors {
                // Successfully decoded without errors
                return Ok(encoding.name().to_string());
            }
        }
    }
    
    // If detection worked with reasonable confidence, return it
    if confidence > 0.5 {
        return Ok(detected_charset.to_string());
    }
    
    // Fallback to UTF-8 if nothing else works
    Ok("UTF-8".to_string())
}

/// Reads a file with the specified encoding
#[pyfunction]
fn read_file_with_encoding(file_path: String, encoding: String) -> PyResult<String> {
    // Read the file as bytes
    let path = Path::new(&file_path);
    let mut file = File::open(path).map_err(|e| {
        PyIOError::new_err(format!("Failed to open file: {}", e))
    })?;
    
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).map_err(|e| {
        PyIOError::new_err(format!("Failed to read file: {}", e))
    })?;
    
    // Try to decode with the specified encoding
    if let Some(enc) = encoding_rs::Encoding::for_label(encoding.as_bytes()) {
        let (decoded, _, had_errors) = enc.decode(&buffer);
        if had_errors {
            return Err(PyIOError::new_err(format!("Failed to decode file with encoding: {}", encoding)));
        }
        Ok(decoded.to_string())
    } else {
        Err(PyIOError::new_err(format!("Unknown encoding: {}", encoding)))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn _internal(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(detect_encoding, m)?)?;
    m.add_function(wrap_pyfunction!(read_file_with_encoding, m)?)?;
    Ok(())
}
