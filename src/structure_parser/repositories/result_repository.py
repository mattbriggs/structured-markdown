"""Result repository — saves parse results to disk."""
from __future__ import annotations

import json
from pathlib import Path

from structure_parser.contracts.parse_run_result import ParseRunResult
from structure_parser.contracts.parsed_document import ParsedDocument


def save_document(doc: ParsedDocument, output_path: Path) -> None:
    """Save a ParsedDocument as JSON to the given path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = doc.model_dump(mode="json", by_alias=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_run_result(result: ParseRunResult, output_path: Path) -> None:
    """Save a ParseRunResult as JSON to the given path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = result.model_dump(mode="json", by_alias=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
