#!/usr/bin/env python3
"""
Example usage of charset-normalizer-rs

This example demonstrates how to use the library to detect
file encoding and read files with different encodings.
"""

import sys
import tempfile
import os
from charset_normalizer_rs import detect_encoding, read_file_with_encoding


def create_sample_files():
    """Create sample files with different encodings for demonstration"""
    samples = []
    
    # UTF-8 file
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='_utf8.txt') as f:
        f.write("This is a UTF-8 file with special characters: café, naïve, 日本語")
        samples.append(('UTF-8 Sample', f.name))
    
    # Latin-1 file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='_latin1.txt') as f:
        f.write("This is a Latin-1 file: São Paulo, México".encode('latin-1'))
        samples.append(('Latin-1 Sample', f.name))
    
    # ASCII file
    with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', delete=False, suffix='_ascii.txt') as f:
        f.write("This is a simple ASCII file without special characters.")
        samples.append(('ASCII Sample', f.name))
    
    return samples


def main():
    """Main example function"""
    print("Charset Normalizer RS - Example Usage")
    print("=" * 50)
    print()
    
    # Create sample files
    samples = create_sample_files()
    
    try:
        for name, filepath in samples:
            print(f"{name}: {os.path.basename(filepath)}")
            print("-" * 50)
            
            # Detect encoding
            detected = detect_encoding(filepath)
            print(f"Detected encoding: {detected}")
            
            # Read file with detected encoding
            content = read_file_with_encoding(filepath, detected)
            print(f"Content: {content}")
            print()
        
        # Example with user-provided file
        if len(sys.argv) > 1:
            user_file = sys.argv[1]
            print(f"User-provided file: {user_file}")
            print("-" * 50)
            
            try:
                detected = detect_encoding(user_file)
                print(f"Detected encoding: {detected}")
                
                content = read_file_with_encoding(user_file, detected)
                print(f"Content preview (first 200 chars):")
                print(content[:200])
                if len(content) > 200:
                    print("...")
            except Exception as e:
                print(f"Error processing file: {e}")
    
    finally:
        # Clean up sample files
        for _, filepath in samples:
            try:
                os.unlink(filepath)
            except:
                pass


if __name__ == "__main__":
    main()
