"""Structure reporter — formats DocumentStructure for human consumption."""
from __future__ import annotations
from structure_parser.contracts.structure import DocumentStructure, StructuralNode


def report_structure(structure: DocumentStructure) -> str:
    """Render a DocumentStructure as an indented tree."""
    lines: list[str] = [
        f"Document structure:",
        f"  Headings: {structure.heading_count}",
        f"  Max depth: {structure.max_depth}",
        f"  Has title: {structure.has_title}",
        "",
    ]
    _render(structure.root, lines, indent=0)
    return "\n".join(lines)


def _render(node: StructuralNode, lines: list[str], indent: int) -> None:
    prefix = "  " * indent
    if node.node_type == "document":
        lines.append(f"{prefix}[document]")
    else:
        level = f"H{node.level}" if node.level else ""
        title = node.title or "(untitled)"
        lines.append(f"{prefix}{level} {title}  ({node.path})")
    for child in node.children:
        _render(child, lines, indent + 1)
