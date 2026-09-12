"""
Quick manual test: python -m nexora_ocr.cli path/to/label.jpg
Prints the structured JSON to stdout -- this is the same JSON Person 2's
backend receives from scan_label().
"""

import argparse
import json
import sys

from .pipeline import scan_label


def main():
    parser = argparse.ArgumentParser(description="Run the NEXORA OCR + extraction pipeline on one label file.")
    parser.add_argument("file", help="Path to a .jpg/.jpeg/.png/.pdf label file")
    parser.add_argument("--lang", nargs="*", default=None, help="EasyOCR language codes, e.g. en hi")
    args = parser.parse_args()

    try:
        result = scan_label(args.file, languages=args.lang)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
