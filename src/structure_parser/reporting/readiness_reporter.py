"""Readiness reporter — formats TransformReadiness for human consumption."""
from __future__ import annotations
from structure_parser.contracts.transform_readiness import TransformReadiness


def report_readiness(readiness: TransformReadiness) -> str:
    """Format a TransformReadiness result as a human-readable report."""
    if not readiness.targets:
        return "No readiness targets evaluated."

    lines: list[str] = [f"Transform readiness:"]
    if readiness.source_path:
        lines[0] += f" {readiness.source_path}"
    lines.append("")

    _STATUS_ICONS = {
        "ready": "+",
        "degraded": "~",
        "blocked": "-",
        "not_evaluated": "?",
    }

    for t in readiness.targets:
        status_icon = _STATUS_ICONS.get(t.status.value, "?")
        lines.append(f"  [{status_icon}] {t.target}: {t.status.value.upper()}")
        for p in t.prerequisites_met:
            lines.append(f"      + {p}")
        for p in t.prerequisites_missing:
            lines.append(f"      - {p}")

    return "\n".join(lines)
