"""Internal raw parse model: adapter output, enrichment input."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from structure_parser.domain.enums import SourceFormat


class RawNode(BaseModel):
    node_type: str  # "heading", "paragraph", "list", "list_item", "code_block", "blockquote",
    # "table", "table_row", "table_cell", "hr", "html_block", "fence", "image", "link",
    # "text", "softbreak", "hardbreak", "em", "strong", "code_inline", "front_matter"
    tag: str = ""  # h1, h2, p, ul, ol, li, pre, blockquote, etc.
    content: str = ""  # raw text or markdown source
    children: list[RawNode] = Field(default_factory=list)
    attrs: dict[str, Any] = Field(default_factory=dict)  # href, src, alt, level, language, etc.
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    level: int | None = None  # heading level


class RawParseModel(BaseModel):
    schema_version: str = "1"
    source_format: SourceFormat
    source_path: str
    content_hash: str | None = None
    front_matter: dict[str, Any] = Field(default_factory=dict)
    front_matter_raw: str | None = None
    front_matter_error: str | None = None
    nodes: list[RawNode] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)
