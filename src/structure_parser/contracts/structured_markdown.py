"""Article/Unit/Component/Attribute hierarchy for structured Markdown content."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from structure_parser.contracts.provenance import SourceSpan
from structure_parser.domain.enums import (
    ArticleType,
    AttributeType,
    ComponentType,
    InformationType,
    ProcedureRepresentation,
    SourceFormat,
    TriageStatus,
    UnitType,
)


class Attribute(BaseModel):
    att_type: AttributeType
    att_id: str | None = None
    markdown: str | None = None
    html: str | None = None
    text: str | None = None
    href: str | None = None
    target: str | None = None
    source: str | None = None  # image src
    alt_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: SourceSpan | None = None
    content: list[Attribute] = Field(default_factory=list)
    triage_status: TriageStatus = TriageStatus.known


class Component(BaseModel):
    component_type: ComponentType
    component_id: str | None = None
    markdown: str | None = None
    html: str | None = None
    text: str | None = None
    level: int | None = None
    language: str | None = None
    code: str | None = None
    alert_type: str | None = None
    href: str | None = None
    alt_text: str | None = None
    count: int | None = None
    order: int | None = None
    column_count: int | None = None
    row_count: int | None = None
    row_index: int | None = None
    row_role: str | None = None
    cell_role: str | None = None
    column_index: int | None = None
    colspan: int | None = None
    rowspan: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: SourceSpan | None = None
    content: list[Attribute | Component] = Field(default_factory=list)
    triage_status: TriageStatus = TriageStatus.known


class Unit(BaseModel):
    unit_type: UnitType
    unit_id: str | None = None
    information_type: InformationType = InformationType.unknown
    title: str | None = None
    triage_status: TriageStatus = TriageStatus.known
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: SourceSpan | None = None
    procedure_representation: ProcedureRepresentation | None = None
    term: str | None = None
    content: list[Component] = Field(default_factory=list)


class StructuredContent(BaseModel):
    schema_version: str = "1"
    schema_name: str = Field(default="artArticle.schema.json", serialization_alias="schema")
    version: str = "0.1.0"

    model_config = {"populate_by_name": True}
    article_id: str | None = None
    article_type: ArticleType = ArticleType.unknown
    dita_type: str | None = None
    information_type: InformationType = InformationType.unknown
    title: str | None = None
    triage_status: TriageStatus = TriageStatus.unknown
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: dict[str, Any] = Field(default_factory=dict)
    content: list[Unit] = Field(default_factory=list)
