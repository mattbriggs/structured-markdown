"""Reference models for links, images, anchors, and includes."""

from pydantic import BaseModel, Field

from structure_parser.domain.enums import ResolutionState


class Reference(BaseModel):
    schema_version: str = "1"
    ref_type: str  # "link", "image", "anchor", "include"
    href: str
    text: str | None = None
    alt_text: str | None = None
    state: ResolutionState = ResolutionState.not_attempted
    resolved_path: str | None = None
    source_path: str | None = None
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
