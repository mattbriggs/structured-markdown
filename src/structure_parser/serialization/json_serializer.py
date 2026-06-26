"""JSON serializer — serializes Pydantic contracts to stable JSON."""
from __future__ import annotations

import json
from typing import Any

from structure_parser.contracts.parse_run_result import ParseRunResult
from structure_parser.contracts.parsed_document import ParsedDocument


def serialize_document(doc: ParsedDocument, indent: int = 2) -> str:
    """Serialize a ParsedDocument to JSON string."""
    data = doc.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(data, indent=indent, ensure_ascii=False)


def serialize_run_result(result: ParseRunResult, indent: int = 2) -> str:
    """Serialize a ParseRunResult to JSON string."""
    data = result.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(data, indent=indent, ensure_ascii=False)


def deserialize_document(json_str: str) -> dict[str, Any]:
    """Parse a JSON string to a dict (does not reconstruct Pydantic model)."""
    return json.loads(json_str)
