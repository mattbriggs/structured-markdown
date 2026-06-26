"""Reference reporter — formats references for human consumption."""
from __future__ import annotations

from structure_parser.contracts.references import Reference


def report_references(references: list[Reference]) -> str:
    """Format a reference list as a table."""
    if not references:
        return "No references found."

    lines = [f"{'Type':<8}  {'State':<15}  {'Href'}"]
    lines.append("-" * 70)
    for ref in references:
        loc = f":{ref.start_line}" if ref.start_line else ""
        lines.append(f"{ref.ref_type:<8}  {ref.state.value:<15}  {ref.href}{loc}")

    by_state: dict[str, int] = {}
    for ref in references:
        by_state.setdefault(ref.state.value, 0)
        by_state[ref.state.value] += 1

    lines.append("")
    for state, count in sorted(by_state.items()):
        lines.append(f"  {state}: {count}")

    return "\n".join(lines)
