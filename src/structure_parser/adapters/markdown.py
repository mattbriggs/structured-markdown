"""Markdown format adapter using markdown-it-py."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.raw import RawNode, RawParseModel
from structure_parser.domain.enums import SourceFormat
from structure_parser.domain.errors import AdapterError


class MarkdownAdapter:
    """Adapter for .md and .markdown source files."""

    source_format = "markdown"
    supported_extensions = (".md", ".markdown")

    def __init__(self) -> None:
        self._md = (
            MarkdownIt("commonmark", {"typographer": False})
            .use(front_matter_plugin)
            .enable("table")
        )

    def parse(self, path: Path, config: ParserConfig) -> RawParseModel:
        """Parse a Markdown file into a RawParseModel."""
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AdapterError(f"Cannot read {path}: {exc}", path=str(path)) from exc

        content_hash = hashlib.sha256(source.encode()).hexdigest()

        # Extract and strip front matter before passing to markdown-it
        front_matter: dict[str, Any] = {}
        front_matter_raw: str | None = None
        front_matter_error: str | None = None
        parse_errors: list[str] = []

        tokens = self._md.parse(source)

        # Extract front matter from tokens
        for tok in tokens:
            if tok.type == "front_matter":
                front_matter_raw = tok.content
                try:
                    parsed = yaml.safe_load(tok.content)
                    if isinstance(parsed, dict):
                        front_matter = parsed
                    elif parsed is not None:
                        front_matter_error = "Front matter must be a YAML mapping"
                except yaml.YAMLError as exc:
                    front_matter_error = str(exc)
                break

        nodes = _tokens_to_nodes(tokens)

        return RawParseModel(
            source_format=SourceFormat.markdown,
            source_path=str(path),
            content_hash=content_hash,
            front_matter=front_matter,
            front_matter_raw=front_matter_raw,
            front_matter_error=front_matter_error,
            nodes=nodes,
            parse_errors=parse_errors,
        )


# ----- Token → RawNode conversion -----

def _tokens_to_nodes(tokens: list) -> list[RawNode]:
    """Convert a flat token list from markdown-it into nested RawNodes."""
    nodes: list[RawNode] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # Skip front matter — already extracted
        if tok.type == "front_matter":
            i += 1
            continue

        # Headings
        if tok.type == "heading_open":
            level = int(tok.tag[1])  # h1 -> 1
            map_ = tok.map or [0, 0]
            # Collect inline content from next token
            inline_children: list[RawNode] = []
            text_content = ""
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                inline_tok = tokens[i + 1]
                text_content = inline_tok.content
                if inline_tok.children:
                    inline_children = _inline_tokens_to_nodes(inline_tok.children)
                i += 1  # consume inline
            # consume heading_close
            if i + 1 < len(tokens) and tokens[i + 1].type == "heading_close":
                i += 1
            nodes.append(RawNode(
                node_type="heading",
                tag=tok.tag,
                content=text_content,
                children=inline_children,
                level=level,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Paragraphs
        elif tok.type == "paragraph_open":
            map_ = tok.map or [0, 0]
            inline_children = []
            text_content = ""
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                inline_tok = tokens[i + 1]
                text_content = inline_tok.content
                if inline_tok.children:
                    inline_children = _inline_tokens_to_nodes(inline_tok.children)
                i += 1
            if i + 1 < len(tokens) and tokens[i + 1].type == "paragraph_close":
                i += 1
            nodes.append(RawNode(
                node_type="paragraph",
                tag="p",
                content=text_content,
                children=inline_children,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Fenced code blocks
        elif tok.type == "fence":
            map_ = tok.map or [0, 0]
            lang = tok.info.strip().split()[0] if tok.info.strip() else ""
            nodes.append(RawNode(
                node_type="code_block",
                tag="pre",
                content=tok.content.rstrip("\n"),
                attrs={"language": lang},
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Code blocks (indented)
        elif tok.type == "code_block":
            map_ = tok.map or [0, 0]
            nodes.append(RawNode(
                node_type="code_block",
                tag="pre",
                content=tok.content.rstrip("\n"),
                attrs={"language": ""},
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Blockquotes (may contain GitHub Alerts)
        elif tok.type == "blockquote_open":
            map_ = tok.map or [0, 0]
            # Find matching close and extract children
            depth = 1
            j = i + 1
            inner_tokens = []
            while j < len(tokens) and depth > 0:
                if tokens[j].type == "blockquote_open":
                    depth += 1
                elif tokens[j].type == "blockquote_close":
                    depth -= 1
                    if depth == 0:
                        break
                inner_tokens.append(tokens[j])
                j += 1
            i = j  # skip to blockquote_close

            inner_nodes = _tokens_to_nodes(inner_tokens)

            # Detect GitHub Alert: first paragraph starts with "> [!TYPE]"
            alert_type = _detect_alert_type(inner_tokens)

            nodes.append(RawNode(
                node_type="blockquote",
                tag="blockquote",
                attrs={"alert_type": alert_type} if alert_type else {},
                children=inner_nodes,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Ordered / unordered lists
        elif tok.type in ("bullet_list_open", "ordered_list_open"):
            map_ = tok.map or [0, 0]
            tag = "ul" if tok.type == "bullet_list_open" else "ol"
            depth = 1
            j = i + 1
            inner_tokens = []
            while j < len(tokens) and depth > 0:
                if tokens[j].type in ("bullet_list_open", "ordered_list_open"):
                    depth += 1
                elif tokens[j].type in ("bullet_list_close", "ordered_list_close"):
                    depth -= 1
                    if depth == 0:
                        break
                inner_tokens.append(tokens[j])
                j += 1
            i = j
            items = _extract_list_items(inner_tokens)
            nodes.append(RawNode(
                node_type="list",
                tag=tag,
                children=items,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Tables
        elif tok.type == "table_open":
            map_ = tok.map or [0, 0]
            j = i + 1
            inner_tokens = []
            depth = 1
            while j < len(tokens) and depth > 0:
                if tokens[j].type == "table_open":
                    depth += 1
                elif tokens[j].type == "table_close":
                    depth -= 1
                    if depth == 0:
                        break
                inner_tokens.append(tokens[j])
                j += 1
            i = j
            rows = _extract_table_rows(inner_tokens)
            nodes.append(RawNode(
                node_type="table",
                tag="table",
                children=rows,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # Horizontal rule
        elif tok.type == "hr":
            map_ = tok.map or [0, 0]
            nodes.append(RawNode(
                node_type="hr",
                tag="hr",
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        # HTML block
        elif tok.type == "html_block":
            map_ = tok.map or [0, 0]
            nodes.append(RawNode(
                node_type="html_block",
                tag="div",
                content=tok.content,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))

        i += 1

    return nodes


def _inline_tokens_to_nodes(tokens: list) -> list[RawNode]:
    """Convert markdown-it inline tokens to RawNodes."""
    nodes: list[RawNode] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok.type == "text":
            nodes.append(RawNode(node_type="text", tag="span", content=tok.content))

        elif tok.type == "softbreak":
            nodes.append(RawNode(node_type="softbreak", tag="br", content="\n"))

        elif tok.type == "hardbreak":
            nodes.append(RawNode(node_type="hardbreak", tag="br", content="\n"))

        elif tok.type == "strong_open":
            # Collect children until strong_close
            j = i + 1
            inner = []
            while j < len(tokens) and tokens[j].type != "strong_close":
                inner.append(tokens[j])
                j += 1
            i = j
            text = "".join(t.content for t in inner if t.type == "text")
            children = _inline_tokens_to_nodes(inner)
            nodes.append(RawNode(
                node_type="strong",
                tag="strong",
                content=text,
                children=children,
            ))

        elif tok.type == "em_open":
            j = i + 1
            inner = []
            while j < len(tokens) and tokens[j].type != "em_close":
                inner.append(tokens[j])
                j += 1
            i = j
            text = "".join(t.content for t in inner if t.type == "text")
            children = _inline_tokens_to_nodes(inner)
            nodes.append(RawNode(
                node_type="em",
                tag="em",
                content=text,
                children=children,
            ))

        elif tok.type == "code_inline":
            nodes.append(RawNode(node_type="code_inline", tag="code", content=tok.content))

        elif tok.type == "link_open":
            href = dict(tok.attrs or {}).get("href", "")
            j = i + 1
            link_text = ""
            while j < len(tokens) and tokens[j].type != "link_close":
                if tokens[j].type == "text":
                    link_text += tokens[j].content
                j += 1
            i = j
            nodes.append(RawNode(
                node_type="link",
                tag="a",
                content=link_text,
                attrs={"href": href},
            ))

        elif tok.type == "image":
            src = dict(tok.attrs or {}).get("src", "")
            alt = tok.content or ""
            nodes.append(RawNode(
                node_type="image",
                tag="img",
                content=alt,
                attrs={"src": src, "alt": alt},
            ))

        i += 1

    return nodes


def _detect_alert_type(tokens: list) -> str | None:
    """Detect GitHub Alert type from blockquote content tokens."""
    for tok in tokens:
        if tok.type == "inline" and tok.content:
            m = re.match(
                r"^\[!(NOTE|TIP|IMPORTANT|CAUTION|WARNING|PUBLIC-PREVIEW)\]",
                tok.content.strip(),
                re.I,
            )
            if m:
                return m.group(1).lower()
    return None


def _extract_list_items(tokens: list) -> list[RawNode]:
    """Extract list_item RawNodes from a flat token list."""
    items: list[RawNode] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "list_item_open":
            map_ = tok.map or [0, 0]
            j = i + 1
            inner = []
            depth = 1
            while j < len(tokens) and depth > 0:
                if tokens[j].type == "list_item_open":
                    depth += 1
                elif tokens[j].type == "list_item_close":
                    depth -= 1
                    if depth == 0:
                        break
                inner.append(tokens[j])
                j += 1
            i = j

            # Get inline text from paragraph_open / inline / paragraph_close
            item_children: list[RawNode] = []
            item_text = ""
            for inner_tok in inner:
                if inner_tok.type == "inline":
                    item_text = inner_tok.content
                    if inner_tok.children:
                        item_children = _inline_tokens_to_nodes(inner_tok.children)

            # Also recurse for nested lists
            nested = _tokens_to_nodes(inner)

            items.append(RawNode(
                node_type="list_item",
                tag="li",
                content=item_text,
                children=item_children or nested,
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))
        i += 1
    return items


def _extract_table_rows(tokens: list) -> list[RawNode]:
    """Extract table_row RawNodes from a flat token list."""
    rows: list[RawNode] = []
    in_head = False
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "thead_open":
            in_head = True
        elif tok.type == "tbody_open":
            in_head = False
        elif tok.type == "tr_open":
            map_ = tok.map or [0, 0]
            row_role = "header" if in_head else "body"
            j = i + 1
            cells: list[RawNode] = []
            while j < len(tokens) and tokens[j].type != "tr_close":
                cell_tok = tokens[j]
                if cell_tok.type in ("th_open", "td_open"):
                    cell_role = "header" if cell_tok.type == "th_open" else "body"
                    k = j + 1
                    cell_text = ""
                    cell_children: list[RawNode] = []
                    close_type = "th_close" if cell_tok.type == "th_open" else "td_close"
                    while k < len(tokens) and tokens[k].type != close_type:
                        if tokens[k].type == "inline":
                            cell_text = tokens[k].content
                            if tokens[k].children:
                                cell_children = _inline_tokens_to_nodes(tokens[k].children)
                        k += 1
                    j = k
                    cells.append(RawNode(
                        node_type="table_cell",
                        tag="td" if cell_tok.type == "td_open" else "th",
                        content=cell_text,
                        children=cell_children,
                        attrs={"cell_role": cell_role},
                    ))
                j += 1
            i = j
            rows.append(RawNode(
                node_type="table_row",
                tag="tr",
                children=cells,
                attrs={"row_role": row_role},
                start_line=map_[0] + 1 if map_ else None,
                end_line=map_[1] if map_ else None,
            ))
        i += 1
    return rows
