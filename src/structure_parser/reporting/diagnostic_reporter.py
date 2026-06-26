"""Diagnostic reporter — formats diagnostics for human consumption."""
from __future__ import annotations

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.domain.enums import Severity
from structure_parser.validation.author_feedback import format_feedback


def report_diagnostics(
    diagnostics: list[Diagnostic],
    source_path: str | None = None,
    include_info: bool = True,
) -> str:
    """Format diagnostics into a human-readable report."""
    return format_feedback(diagnostics, source_path=source_path)


def report_diagnostics_by_file(
    docs: list,
    include_info: bool = False,
) -> str:
    """Format diagnostics grouped by source file."""
    lines: list[str] = []
    for doc in docs:
        if not doc.diagnostics:
            continue
        visible = doc.diagnostics if include_info else [
            d for d in doc.diagnostics if d.severity != Severity.info
        ]
        if visible:
            lines.append(format_feedback(visible, source_path=doc.source_path))
            lines.append("")
    return "\n".join(lines)
