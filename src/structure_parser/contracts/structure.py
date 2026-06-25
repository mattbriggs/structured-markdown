"""Document structure models for the hierarchical node tree."""

from __future__ import annotations

from pydantic import BaseModel, Field

from structure_parser.contracts.provenance import SourceSpan
from structure_parser.domain.enums import TriageStatus


class StructuralNode(BaseModel):
    node_id: str
    node_type: str  # "document", "section", "heading", "block"
    title: str | None = None
    level: int | None = None
    path: str  # e.g. "/0/1/2" positional path
    children: list[StructuralNode] = Field(default_factory=list)
    source: SourceSpan | None = None
    triage_status: TriageStatus = TriageStatus.known


class DocumentStructure(BaseModel):
    root: StructuralNode
    heading_count: int = 0
    max_depth: int = 0
    has_title: bool = False
