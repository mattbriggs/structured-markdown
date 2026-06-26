#!/usr/bin/env python3
"""Validate test fixtures against expected contract behavior.

Run with: python tools/validate_fixtures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from structure_parser import parse_file

FIXTURES = [
    Path("tests/fixtures/markdown/clean.md"),
    Path("tests/fixtures/markdown/complex.md"),
    Path("tests/fixtures/markdown/known_failure.md"),
    Path("tests/fixtures/markdown/unknown_classification.md"),
]


def main() -> None:
    root = Path(__file__).parent.parent
    all_pass = True

    for fixture_rel in FIXTURES:
        fixture = root / fixture_rel
        if not fixture.exists():
            print(f"MISSING: {fixture_rel}")
            all_pass = False
            continue

        doc = parse_file(fixture)
        errors = [d for d in doc.diagnostics if d.code == "SP-099"]

        if errors:
            print(f"FAIL: {fixture_rel.name} — internal errors: {len(errors)}")
            for e in errors:
                print(f"  {e.code}: {e.message}")
            all_pass = False
        else:
            unit_count = len(doc.structured_content.content) if doc.structured_content else 0
            status = f"title={doc.title!r}, units={unit_count}, diags={len(doc.diagnostics)}"
            print(f"PASS: {fixture_rel.name} — {status}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
