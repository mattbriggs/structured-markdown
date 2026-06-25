"""Rendered HTML adapter using lxml."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any

try:
    from lxml import etree, html as lxml_html
    _LXML_AVAILABLE = True
except ImportError:
    _LXML_AVAILABLE = False

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.raw import RawNode, RawParseModel
from structure_parser.domain.enums import SourceFormat
from structure_parser.domain.errors import AdapterError


class HtmlAdapter:
    """Adapter for .html and .htm source files using lxml."""

    source_format = "html5"
    supported_extensions = (".html", ".htm")

    def parse(self, path: Path, config: ParserConfig) -> RawParseModel:
        """Parse an HTML file into a RawParseModel."""
        if not _LXML_AVAILABLE:
            raise AdapterError(
                "lxml is required for HTML parsing. Install it with: pip install lxml",
                path=str(path),
            )

        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AdapterError(f"Cannot read {path}: {exc}", path=str(path)) from exc

        content_hash = hashlib.sha256(source.encode()).hexdigest()
        parse_errors: list[str] = []

        try:
            doc = lxml_html.fromstring(source)
        except Exception as exc:
            parse_errors.append(str(exc))
            return RawParseModel(
                source_format=SourceFormat.html5,
                source_path=str(path),
                content_hash=content_hash,
                nodes=[],
                parse_errors=parse_errors,
            )

        # Extract body content
        body = doc.find(".//body")
        if body is None:
            body = doc

        nodes = _element_to_nodes(body)

        return RawParseModel(
            source_format=SourceFormat.html5,
            source_path=str(path),
            content_hash=content_hash,
            nodes=nodes,
            parse_errors=parse_errors,
        )


def _element_to_nodes(element: Any) -> list[RawNode]:
    """Convert lxml elements to RawNodes."""
    nodes: list[RawNode] = []

    for child in element:
        tag = child.tag if isinstance(child.tag, str) else ""
        tag_lower = tag.lower()

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag_lower[1])
            text = (child.text_content() or "").strip()
            nodes.append(RawNode(
                node_type="heading",
                tag=tag_lower,
                content=text,
                level=level,
            ))

        elif tag_lower == "p":
            text = (child.text_content() or "").strip()
            inline = _inline_elements(child)
            nodes.append(RawNode(
                node_type="paragraph",
                tag="p",
                content=text,
                children=inline,
            ))

        elif tag_lower in ("pre", "code"):
            code_el = child.find(".//code") if tag_lower == "pre" else child
            lang = ""
            if code_el is not None:
                cls = code_el.get("class", "")
                for part in cls.split():
                    if part.startswith("language-"):
                        lang = part[9:]
            text = (child.text_content() or "").strip()
            nodes.append(RawNode(
                node_type="code_block",
                tag="pre",
                content=text,
                attrs={"language": lang},
            ))

        elif tag_lower in ("ul", "ol"):
            items = _list_items(child)
            nodes.append(RawNode(
                node_type="list",
                tag=tag_lower,
                children=items,
            ))

        elif tag_lower == "blockquote":
            inner = _element_to_nodes(child)
            nodes.append(RawNode(
                node_type="blockquote",
                tag="blockquote",
                children=inner,
            ))

        elif tag_lower == "table":
            rows = _table_rows(child)
            nodes.append(RawNode(
                node_type="table",
                tag="table",
                children=rows,
            ))

        elif tag_lower == "hr":
            nodes.append(RawNode(node_type="hr", tag="hr"))

        elif tag_lower in ("div", "section", "article", "main"):
            # Recurse into container elements
            nodes.extend(_element_to_nodes(child))

        # Skip script, style, nav, footer etc.

    return nodes


def _inline_elements(element: Any) -> list[RawNode]:
    """Extract inline children from a paragraph or similar element."""
    nodes: list[RawNode] = []

    def _walk(el: Any, nodes: list[RawNode]) -> None:
        if el.text:
            nodes.append(RawNode(node_type="text", tag="span", content=el.text))
        for child in el:
            tag = (child.tag or "").lower() if isinstance(child.tag, str) else ""
            if tag in ("strong", "b"):
                text = child.text_content() or ""
                nodes.append(RawNode(node_type="strong", tag="strong", content=text))
            elif tag in ("em", "i"):
                text = child.text_content() or ""
                nodes.append(RawNode(node_type="em", tag="em", content=text))
            elif tag == "code":
                text = child.text_content() or ""
                nodes.append(RawNode(node_type="code_inline", tag="code", content=text))
            elif tag == "a":
                href = child.get("href", "")
                text = child.text_content() or ""
                nodes.append(RawNode(node_type="link", tag="a", content=text, attrs={"href": href}))
            elif tag == "img":
                src = child.get("src", "")
                alt = child.get("alt", "")
                nodes.append(RawNode(node_type="image", tag="img", content=alt, attrs={"src": src, "alt": alt}))
            if child.tail:
                nodes.append(RawNode(node_type="text", tag="span", content=child.tail))

    _walk(element, nodes)
    return nodes


def _list_items(element: Any) -> list[RawNode]:
    items: list[RawNode] = []
    for li in element.findall("li"):
        text = (li.text_content() or "").strip()
        children = _inline_elements(li)
        items.append(RawNode(node_type="list_item", tag="li", content=text, children=children))
    return items


def _table_rows(element: Any) -> list[RawNode]:
    rows: list[RawNode] = []
    for section in element:
        sec_tag = (section.tag or "").lower() if isinstance(section.tag, str) else ""
        in_head = sec_tag == "thead"
        items = [section] if sec_tag == "tr" else list(section)
        for row in items:
            row_tag = (row.tag or "").lower() if isinstance(row.tag, str) else ""
            if row_tag != "tr":
                continue
            row_role = "header" if in_head else "body"
            cells: list[RawNode] = []
            for cell in row:
                cell_tag = (cell.tag or "").lower() if isinstance(cell.tag, str) else ""
                if cell_tag not in ("th", "td"):
                    continue
                cell_role = "header" if cell_tag == "th" else "body"
                text = (cell.text_content() or "").strip()
                children = _inline_elements(cell)
                cells.append(RawNode(
                    node_type="table_cell",
                    tag=cell_tag,
                    content=text,
                    children=children,
                    attrs={"cell_role": cell_role},
                ))
            rows.append(RawNode(
                node_type="table_row",
                tag="tr",
                children=cells,
                attrs={"row_role": row_role},
            ))
    return rows
