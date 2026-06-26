"""Structure builder — builds DocumentStructure from raw nodes."""
from __future__ import annotations

import uuid

from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.contracts.provenance import SourceSpan
from structure_parser.contracts.raw import RawParseModel
from structure_parser.contracts.structure import DocumentStructure, StructuralNode
from structure_parser.domain.enums import ProvenanceStatus


def build_structure(raw: RawParseModel) -> tuple[DocumentStructure, list[Diagnostic]]:
    """Build a DocumentStructure from a RawParseModel's node list."""
    diags: list[Diagnostic] = []
    heading_nodes = [n for n in raw.nodes if n.node_type == "heading"]

    has_title = any(n.level == 1 for n in heading_nodes)
    if not has_title:
        diags.append(DiagnosticFactory.missing_title(source_path=raw.source_path))

    # Check for heading level skips
    prev_level = 0
    for node in heading_nodes:
        current = node.level or 1
        if prev_level > 0 and current > prev_level + 1:
            diags.append(DiagnosticFactory.heading_level_skipped(
                from_level=prev_level,
                to_level=current,
                source_path=raw.source_path,
                start_line=node.start_line,
            ))
        prev_level = current

    # Build structural tree
    root = StructuralNode(
        node_id="root",
        node_type="document",
        title=None,
        path="/",
        source=SourceSpan(
            source_path=raw.source_path, provenance_status=ProvenanceStatus.unavailable
        ),
    )

    stack: list[StructuralNode] = [root]
    level_stack: list[int] = [0]
    position_counters: list[int] = [0]

    for node in raw.nodes:
        if node.node_type != "heading":
            continue
        level = node.level or 1

        # Pop stack to find parent
        while len(level_stack) > 1 and level_stack[-1] >= level:
            stack.pop()
            level_stack.pop()
            position_counters.pop()

        parent = stack[-1]
        position_counters[-1] += 1
        path = parent.path.rstrip("/") + f"/{position_counters[-1]}"

        span = SourceSpan(
            source_path=raw.source_path,
            start_line=node.start_line,
            end_line=node.end_line,
            provenance_status=(
                ProvenanceStatus.available if node.start_line else ProvenanceStatus.unavailable
            ),
        )

        section = StructuralNode(
            node_id=f"h{level}-{uuid.uuid4().hex[:6]}",
            node_type="section",
            title=node.content,
            level=level,
            path=path,
            source=span,
        )
        parent.children.append(section)
        stack.append(section)
        level_stack.append(level)
        position_counters.append(0)

    heading_count = len(heading_nodes)
    max_depth = max((n.level or 1 for n in heading_nodes), default=0)

    return DocumentStructure(
        root=root,
        heading_count=heading_count,
        max_depth=max_depth,
        has_title=has_title,
    ), diags
