"""ParsedDocument contract: the primary output of a single-file parse."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.provenance import DocumentProvenance
from structure_parser.contracts.references import Reference
from structure_parser.contracts.structure import DocumentStructure
from structure_parser.contracts.structured_markdown import StructuredContent
from structure_parser.contracts.transform_readiness import TransformReadiness
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.domain.enums import Severity, SourceFormat


class ParsedDocument(BaseModel):
    schema_version: str = "1"
    source_path: str
    source_format: SourceFormat
    provenance: DocumentProvenance | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    title: str | None = None
    structure: DocumentStructure | None = None
    structured_content: StructuredContent | None = None
    references: list[Reference] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    validation: ModelValidationResult | None = None
    readiness: TransformReadiness | None = None

    @property
    def has_errors(self) -> bool:
        return any(d.severity == Severity.error for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.error)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.warning)
