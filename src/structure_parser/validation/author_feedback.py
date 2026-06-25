"""Author-facing feedback — groups diagnostics into actionable messages."""
from __future__ import annotations

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.domain.enums import Severity


def format_feedback(
    diagnostics: list[Diagnostic],
    source_path: str | None = None,
) -> str:
    """Format diagnostics as an author-readable text report.

    Args:
        diagnostics: List of Diagnostic objects to format.
        source_path: Optional source file path shown in the report header.

    Returns:
        A multi-line human-readable string.
    """
    errors = [d for d in diagnostics if d.severity == Severity.error]
    warnings = [d for d in diagnostics if d.severity == Severity.warning]
    infos = [d for d in diagnostics if d.severity == Severity.info]

    lines: list[str] = []
    if source_path:
        lines.append(f"Validation report: {source_path}")
        lines.append("=" * 60)

    if not diagnostics:
        lines.append("No issues found.")
        return "\n".join(lines)

    if errors:
        lines.append(f"\nErrors ({len(errors)}):")
        for d in errors:
            loc = f" [{d.start_line}]" if d.start_line else ""
            lines.append(f"  [{d.code}]{loc} {d.message}")
            if d.detail:
                lines.append(f"    Detail: {d.detail}")
            if d.remediation:
                lines.append(f"    Fix: {d.remediation}")

    if warnings:
        lines.append(f"\nWarnings ({len(warnings)}):")
        for d in warnings:
            loc = f" [{d.start_line}]" if d.start_line else ""
            lines.append(f"  [{d.code}]{loc} {d.message}")
            if d.remediation:
                lines.append(f"    Fix: {d.remediation}")

    if infos:
        lines.append(f"\nInfo ({len(infos)}):")
        for d in infos:
            lines.append(f"  [{d.code}] {d.message}")

    return "\n".join(lines)


def group_by_severity(diagnostics: list[Diagnostic]) -> dict[str, list[Diagnostic]]:
    """Group diagnostics by severity string.

    Returns:
        A dict keyed by Severity value strings ("error", "warning", "info", "debug"),
        each mapping to the corresponding subset of diagnostics.
    """
    result: dict[str, list[Diagnostic]] = {s.value: [] for s in Severity}
    for d in diagnostics:
        result[d.severity.value].append(d)
    return result
