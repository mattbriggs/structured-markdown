"""Provenance models for tracking source location of parsed content."""

from pydantic import BaseModel, Field

from structure_parser.domain.enums import ProvenanceStatus, SourceFormat


class SourceSpan(BaseModel):
    source_path: str | None = None
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    query_path: str | None = None
    provenance_status: ProvenanceStatus = ProvenanceStatus.unavailable


class DocumentProvenance(BaseModel):
    source_path: str
    source_format: SourceFormat
    content_hash: str | None = None
    start_line: int = Field(default=1, ge=1)
    end_line: int | None = Field(default=None, ge=1)
