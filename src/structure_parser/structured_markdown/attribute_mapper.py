"""Maps inline RawNodes to Attribute contracts."""
from __future__ import annotations

import re  # noqa: F401  (available for callers that extend this module)

from structure_parser.contracts.raw import RawNode
from structure_parser.contracts.structured_markdown import Attribute
from structure_parser.domain.enums import AttributeType, TriageStatus
from structure_parser.enrichment.provenance_mapper import node_to_span


def map_inline_nodes(nodes: list[RawNode], source_path: str) -> list[Attribute]:
    """Convert a list of inline RawNodes to Attribute objects."""
    attrs: list[Attribute] = []
    for node in nodes:
        attr = _map_node(node, source_path)
        if attr:
            attrs.append(attr)
    return attrs


def _map_node(node: RawNode, source_path: str) -> Attribute | None:
    span = node_to_span(node, source_path)

    if node.node_type == "text":
        return Attribute(
            att_type=AttributeType.attText,
            text=node.content,
            markdown=node.content,
            provenance=span,
        )

    if node.node_type == "strong":
        inner = map_inline_nodes(node.children, source_path)
        text = node.content or "".join(c.text or "" for c in inner if c.text)
        return Attribute(
            att_type=AttributeType.attStrong,
            text=text,
            markdown=f"**{text}**",
            content=inner,
            provenance=span,
        )

    if node.node_type == "em":
        inner = map_inline_nodes(node.children, source_path)
        text = node.content or "".join(c.text or "" for c in inner if c.text)
        return Attribute(
            att_type=AttributeType.attEmphasis,
            text=text,
            markdown=f"*{text}*",
            content=inner,
            provenance=span,
        )

    if node.node_type == "code_inline":
        return Attribute(
            att_type=AttributeType.attCode,
            text=node.content,
            markdown=f"`{node.content}`",
            provenance=span,
        )

    if node.node_type == "link":
        href = node.attrs.get("href", "")
        text = node.content or ""
        return Attribute(
            att_type=AttributeType.attLink,
            href=href,
            text=text,
            markdown=f"[{text}]({href})",
            provenance=span,
        )

    if node.node_type == "image":
        src = node.attrs.get("src", "")
        alt = node.attrs.get("alt", "")
        return Attribute(
            att_type=AttributeType.attImage,
            source=src,
            alt_text=alt,
            markdown=f"![{alt}]({src})",
            provenance=span,
        )

    # Fallback for any inline node type not explicitly handled above
    return Attribute(
        att_type=AttributeType.attUnknown,
        text=node.content,
        triage_status=TriageStatus.unknown,
        provenance=span,
    )
