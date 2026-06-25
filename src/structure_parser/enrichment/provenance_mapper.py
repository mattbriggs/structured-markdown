"""Maps RawNode instances to SourceSpan provenance objects."""
from __future__ import annotations

from structure_parser.contracts.provenance import SourceSpan
from structure_parser.contracts.raw import RawNode
from structure_parser.domain.enums import ProvenanceStatus


def node_to_span(node: RawNode | None, source_path: str) -> SourceSpan:
    """Convert a RawNode's location information into a SourceSpan.

    Args:
        node: The raw node to extract provenance from. If None, returns a span
              with unavailable provenance status.
        source_path: The path to the source file.

    Returns:
        A SourceSpan with available line numbers where known.
    """
    if node is None:
        return SourceSpan(
            source_path=source_path,
            provenance_status=ProvenanceStatus.unavailable,
        )

    has_start = node.start_line is not None
    has_end = node.end_line is not None

    if has_start and has_end:
        status = ProvenanceStatus.available
    elif has_start or has_end:
        status = ProvenanceStatus.partial
    else:
        status = ProvenanceStatus.unavailable

    return SourceSpan(
        source_path=source_path,
        start_line=node.start_line,
        end_line=node.end_line,
        provenance_status=status,
    )
