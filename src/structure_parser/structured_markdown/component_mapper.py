"""Maps block RawNodes to Component contracts."""
from __future__ import annotations

from structure_parser.contracts.raw import RawNode
from structure_parser.contracts.structured_markdown import Attribute, Component
from structure_parser.domain.enums import AttributeType, ComponentType, TriageStatus
from structure_parser.enrichment.provenance_mapper import node_to_span
from structure_parser.structured_markdown.attribute_mapper import map_inline_nodes


def map_block_node(node: RawNode, source_path: str) -> Component:
    """Convert a block RawNode to a Component."""
    span = node_to_span(node, source_path)

    if node.node_type == "heading":
        level = node.level or 1
        comp_type = {
            1: ComponentType.compHeaderH1,
            2: ComponentType.compHeaderH2,
            3: ComponentType.compHeaderH3,
            4: ComponentType.compHeaderH4,
            5: ComponentType.compHeaderH5,
            6: ComponentType.compHeaderH6,
        }.get(level, ComponentType.compHeaderH1)
        if node.children:
            attrs = map_inline_nodes(node.children, source_path)
        else:
            attrs = [
                Attribute(
                    att_type=AttributeType.attText,
                    text=node.content,
                    markdown=node.content,
                )
            ]
        return Component(
            component_type=comp_type,
            level=level,
            text=node.content,
            markdown=f"{'#' * level} {node.content}",
            source=span,
            content=attrs,
        )

    if node.node_type == "paragraph":
        attrs = map_inline_nodes(node.children, source_path) if node.children else []
        return Component(
            component_type=ComponentType.compParagraph,
            text=node.content,
            markdown=node.content,
            source=span,
            content=attrs,
        )

    if node.node_type == "code_block":
        lang = node.attrs.get("language", "")
        fence = f"```{lang}\n{node.content}```"
        return Component(
            component_type=ComponentType.compBlockCode,
            language=lang,
            code=node.content,
            markdown=fence,
            source=span,
        )

    if node.node_type == "blockquote":
        alert_type = node.attrs.get("alert_type")
        children_comps = [
            map_block_node(c, source_path)
            for c in node.children
            if c.node_type != "heading"
        ]
        if alert_type:
            inner = "\n".join(
                f"> {c.content}" for c in node.children if c.node_type == "paragraph" and c.content
            )
            md = f"> [!{alert_type.upper()}]\n{inner}" if inner else f"> [!{alert_type.upper()}]"
            return Component(
                component_type=ComponentType.compAlert,
                alert_type=alert_type,
                markdown=md,
                source=span,
                content=children_comps,
            )
        inner = "\n".join(
            f"> {c.content}" for c in node.children if c.node_type == "paragraph" and c.content
        )
        return Component(
            component_type=ComponentType.compBlockQuote,
            markdown=inner or "> ...",
            source=span,
            content=children_comps,
        )

    if node.node_type == "list":
        ordered = node.tag == "ol"
        comp_type = (
            ComponentType.compListOrdered if ordered else ComponentType.compListUnordered
        )
        count = len(node.children)
        items = [
            _map_list_item(child, source_path, i + 1)
            for i, child in enumerate(node.children)
        ]
        return Component(
            component_type=comp_type,
            count=count,
            source=span,
            content=items,
        )

    if node.node_type == "table":
        rows = [
            _map_table_row(r, source_path, i + 1) for i, r in enumerate(node.children)
        ]
        row_count = len(rows)
        col_count = max((len(r.content) for r in rows), default=0)
        return Component(
            component_type=ComponentType.compTable,
            row_count=row_count,
            column_count=col_count,
            source=span,
            content=rows,
        )

    if node.node_type == "link":
        href = node.attrs.get("href", "")
        text = node.content or ""
        return Component(
            component_type=ComponentType.compLink,
            href=href,
            text=text,
            markdown=f"[{text}]({href})",
            source=span,
        )

    if node.node_type == "hr":
        return Component(
            component_type=ComponentType.compUnknown,
            text="---",
            markdown="---",
            source=span,
            triage_status=TriageStatus.unknown,
        )

    # Fallback: unknown block node type
    return Component(
        component_type=ComponentType.compUnknown,
        text=node.content,
        markdown=node.content or "",
        source=span,
        triage_status=TriageStatus.unknown,
    )


def _map_list_item(node: RawNode, source_path: str, order: int) -> Component:
    span = node_to_span(node, source_path)

    _inline_types = frozenset(
        {"text", "link", "image", "strong", "em", "code_inline"}
    )
    inline_nodes = [c for c in node.children if c.node_type in _inline_types]
    block_nodes = [c for c in node.children if c.node_type not in _inline_types]

    attrs = map_inline_nodes(inline_nodes, source_path)
    sub_comps = [map_block_node(c, source_path) for c in block_nodes]

    text = node.content or " ".join(c.text or "" for c in attrs if c.text)

    return Component(
        component_type=ComponentType.compListItem,
        text=text,
        markdown=text,
        order=order,
        source=span,
        content=attrs + sub_comps,  # type: ignore[operator]
    )


def _map_table_row(node: RawNode, source_path: str, row_index: int) -> Component:
    span = node_to_span(node, source_path)
    row_role = node.attrs.get("row_role", "body")
    cells = [
        _map_table_cell(c, source_path, i + 1, row_role)
        for i, c in enumerate(node.children)
    ]
    return Component(
        component_type=ComponentType.compTableRow,
        row_index=row_index,
        row_role=row_role,
        source=span,
        content=cells,
    )


def _map_table_cell(
    node: RawNode, source_path: str, col_index: int, row_role: str
) -> Component:
    span = node_to_span(node, source_path)
    cell_role = node.attrs.get(
        "cell_role", "body" if row_role == "body" else "header"
    )
    inline_nodes = node.children if node.children else []
    attrs = map_inline_nodes(inline_nodes, source_path) if inline_nodes else []

    return Component(
        component_type=ComponentType.compTableCell,
        text=node.content,
        markdown=node.content or "",
        column_index=col_index,
        cell_role=cell_role,
        source=span,
        content=attrs,
    )
