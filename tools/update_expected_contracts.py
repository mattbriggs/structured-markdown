#!/usr/bin/env python3
"""Update expected contract JSON fixtures from current parser output.

Run with: python tools/update_expected_contracts.py
WARNING: Only run this when the parser output is known-good.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from structure_parser import parse_file
from structure_parser.serialization.json_serializer import serialize_document

FIXTURES = {
    "clean": Path("tests/fixtures/markdown/clean.md"),
    "complex": Path("tests/fixtures/markdown/complex.md"),
    "unknown_classification": Path("tests/fixtures/markdown/unknown_classification.md"),
}

EXPECTED_DIR = Path("tests/fixtures/expected")


def main() -> None:
    root = Path(__file__).parent.parent
    expected_dir = root / EXPECTED_DIR
    expected_dir.mkdir(parents=True, exist_ok=True)

    for name, fixture_rel in FIXTURES.items():
        fixture = root / fixture_rel
        if not fixture.exists():
            print(f"MISSING: {fixture_rel}")
            continue

        doc = parse_file(fixture)
        output_path = expected_dir / f"{name}.parse.json"
        output_path.write_text(serialize_document(doc), encoding="utf-8")
        print(f"Updated: {output_path.relative_to(root)}")

    print("Done. Review the changes before committing.")


if __name__ == "__main__":
    main()
