"""Reference classifier — extracts and classifies links and images from raw nodes."""
from __future__ import annotations

from structure_parser.contracts.raw import RawNode, RawParseModel
from structure_parser.contracts.references import Reference
from structure_parser.domain.enums import ResolutionState


def classify_references(raw: RawParseModel) -> list[Reference]:
    """Extract and classify all references from a RawParseModel."""
    refs: list[Reference] = []
    _walk_nodes(raw.nodes, raw.source_path, refs)
    return refs


def _walk_nodes(nodes: list[RawNode], source_path: str, refs: list[Reference]) -> None:
    for node in nodes:
        if node.node_type == "link":
            href = node.attrs.get("href", "")
            refs.append(Reference(
                ref_type="link",
                href=href,
                text=node.content,
                state=ResolutionState.not_attempted,
                source_path=source_path,
                start_line=node.start_line,
                end_line=node.end_line,
            ))

        elif node.node_type == "image":
            src = node.attrs.get("src", "")
            alt = node.attrs.get("alt", "")
            refs.append(Reference(
                ref_type="image",
                href=src,
                alt_text=alt,
                state=ResolutionState.not_attempted,
                source_path=source_path,
                start_line=node.start_line,
                end_line=node.end_line,
            ))

        # Recurse into children
        if node.children:
            _walk_nodes(node.children, source_path, refs)
