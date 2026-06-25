#!/usr/bin/env python3
"""Generate JSON Schema files from Pydantic models.

Run with: python tools/generate_json_schemas.py
Output goes to schemas/parser/v1/ and schemas/structured_markdown/v1/
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.parse_run_result import ParseRunResult
from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.references import Reference
from structure_parser.contracts.structured_markdown import StructuredContent

OUTPUT_DIRS = {
    "parser": Path("schemas/parser/v1"),
    "structured_markdown": Path("schemas/structured_markdown/v1"),
}

SCHEMAS = {
    "parser": {
        "ParsedDocument.schema.json": ParsedDocument,
        "ParseRunResult.schema.json": ParseRunResult,
        "Diagnostic.schema.json": Diagnostic,
        "Reference.schema.json": Reference,
    },
    "structured_markdown": {
        "Article.schema.json": StructuredContent,
    },
}

def main() -> None:
    root = Path(__file__).parent.parent
    for section, models in SCHEMAS.items():
        output_dir = root / OUTPUT_DIRS[section]
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, model in models.items():
            schema = model.model_json_schema()
            output_path = output_dir / filename
            output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            print(f"  Generated: {output_path.relative_to(root)}")
    print("Done.")


if __name__ == "__main__":
    main()
