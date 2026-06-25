"""ParseRunResult contract: the aggregate output of a multi-file parse run."""

from __future__ import annotations

from pydantic import BaseModel, Field

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.parsed_document import ParsedDocument


class ParseStats(BaseModel):
    file_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    duration_ms: float | None = None


class ParseRunResult(BaseModel):
    schema_version: str = "1"
    documents: list[ParsedDocument] = Field(default_factory=list)
    run_diagnostics: list[Diagnostic] = Field(default_factory=list)
    stats: ParseStats = Field(default_factory=ParseStats)

    @property
    def success(self) -> bool:
        return not any(d.has_errors for d in self.documents) and not self.run_diagnostics
