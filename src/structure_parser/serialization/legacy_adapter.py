"""Legacy compatibility adapter — placeholder per assumption A-005."""
from __future__ import annotations
from typing import Any
from structure_parser.contracts.parsed_document import ParsedDocument


def to_legacy_projection(doc: ParsedDocument) -> dict[str, Any]:
    """Project a ParsedDocument to a simplified legacy output shape.

    This is a placeholder adapter. The exact legacy shape is pending
    the compatibility field inventory (OQ-R1). Currently returns a
    minimal projection of the most commonly needed fields.
    """
    result: dict[str, Any] = {
        "source_path": doc.source_path,
        "source_format": doc.source_format.value,
        "title": doc.title,
        "metadata": doc.metadata,
        "error_count": doc.error_count,
        "warning_count": doc.warning_count,
    }

    if doc.structured_content:
        result["article_type"] = doc.structured_content.article_type.value
        result["unit_count"] = len(doc.structured_content.content)

    result["diagnostics"] = [
        {
            "code": d.code,
            "severity": d.severity.value,
            "message": d.message,
            "line": d.start_line,
        }
        for d in doc.diagnostics
    ]

    return result
