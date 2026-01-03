"""
Examples of using the charsetrs library

This file demonstrates the main features of charsetrs:
1. Detecting file encodings
2. Converting files between encodings
3. Working with large files using max_sample_size
"""

import os
import tempfile

import charsetrs


def example_1_basic_detection():
    """Example 1: Basic encoding detection"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Encoding Detection")
    print("=" * 60)

    # Create a test file with UTF-8 encoding
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write("Hello World! This is UTF-8 text with special chars: áéíóú ñ 你好")
        temp_file = f.name

    try:
        # Detect the encoding
        encoding = charsetrs.detect(temp_file)
        print(f"\nDetected encoding: {encoding}")
        print("✓ Simple and straightforward!")
    finally:
        os.unlink(temp_file)


def example_2_basic_conversion():
    """Example 2: Basic encoding conversion"""
    print("\n" + "=" * 60)
    print("Example 2: Basic Encoding Conversion")
    print("=" * 60)

    # Create a file with Latin-1 encoding
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        content = "Café, São Paulo, naïve"
        f.write(content.encode("latin-1"))
        temp_file = f.name

    try:
        # Convert to UTF-8
        converted_content = charsetrs.convert(temp_file, to="utf-8")
        print("\nOriginal encoding was auto-detected")
        print(f"Converted to UTF-8: {converted_content}")
        print("✓ Automatic detection and conversion!")
    finally:
        os.unlink(temp_file)


def example_3_large_files():
    """Example 3: Working with large files"""
    print("\n" + "=" * 60)
    print("Example 3: Large File Handling")
    print("=" * 60)

    # Create a large file
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        # Write ~5MB of content
        for _ in range(100000):
            f.write("This is a line of text with UTF-8 chars: áéíóú\n")
        temp_file = f.name

    try:
        # Detect with small sample (faster, less memory)
        encoding_small = charsetrs.detect(temp_file, max_sample_size=512 * 1024)  # 512KB
        print(f"\nDetection with 512KB sample: {encoding_small}")

        # Detect with larger sample (more accurate)
        encoding_large = charsetrs.detect(temp_file, max_sample_size=2 * 1024 * 1024)  # 2MB
        print(f"Detection with 2MB sample: {encoding_large}")

        print("\n✓ Memory-efficient for large files!")
        print("  You can tune max_sample_size based on your needs:")
        print("  - Smaller = faster, less memory")
        print("  - Larger = more accurate")
    finally:
        os.unlink(temp_file)


def example_4_real_world_files():
    """Example 4: Working with real-world sample files"""
    print("\n" + "=" * 60)
    print("Example 4: Real-World Sample Files")
    print("=" * 60)

    sample_files = [
        "tests/data/sample-arabic.txt",
        "tests/data/sample-french.txt",
        "tests/data/sample-korean.txt",
        "tests/data/sample-russian.txt",
    ]

    for file_path in sample_files:
        if os.path.exists(file_path):
            try:
                # Detect encoding
                encoding = charsetrs.detect(file_path)

                # Convert to UTF-8
                content = charsetrs.convert(file_path, to="utf-8")

                filename = os.path.basename(file_path)
                print(f"\n{filename}:")
                print(f"  Encoding: {encoding}")
                print(f"  Size: {len(content)} chars")
                print(f"  Preview: {content[:50]}...")
            except Exception as e:
                print(f"\n{file_path}: Error - {e}")


def example_5_encoding_comparison():
    """Example 5: Comparing different encodings"""
    print("\n" + "=" * 60)
    print("Example 5: Encoding Comparison")
    print("=" * 60)

    text = "Hello: café, naïve, São Paulo"

    encodings_to_test = ["utf-8", "latin-1", "utf-16"]

    print(f"\nOriginal text: {text}")
    print("\nTesting different encodings:")

    for encoding in encodings_to_test:
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
            try:
                f.write(text.encode(encoding))
                temp_file = f.name
            except UnicodeEncodeError:
                print(f"  {encoding}: Cannot encode this text")
                os.unlink(temp_file)
                continue

        try:
            detected = charsetrs.detect(temp_file)
            print(f"  {encoding} → detected as: {detected}")
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CHARSETRS LIBRARY - USAGE EXAMPLES")
    print("=" * 60)

    example_1_basic_detection()
    example_2_basic_conversion()
    example_3_large_files()
    example_4_real_world_files()
    example_5_encoding_comparison()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. charsetrs.detect(file) - Simple encoding detection")
    print("  2. charsetrs.convert(file, to='utf-8') - Easy conversion")
    print("  3. max_sample_size parameter - Control memory vs accuracy")
    print("  4. Works with any file size efficiently")
    print("=" * 60 + "\n")
