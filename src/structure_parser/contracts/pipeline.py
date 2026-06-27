"""Pydantic contracts for repository-scale parser pipeline runs."""
from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.domain.enums import DiagnosticCategory, Severity, SourceFormat

# Pipeline error code constants (PIPE-### namespace, separate from SP-### parser codes)
PIPE_001 = "PIPE-001"
PIPE_002 = "PIPE-002"
PIPE_003 = "PIPE-003"
PIPE_004 = "PIPE-004"
PIPE_005 = "PIPE-005"
PIPE_006 = "PIPE-006"
PIPE_007 = "PIPE-007"
PIPE_099 = "PIPE-099"

_PIPE_META: dict[str, tuple[Severity, str]] = {
    PIPE_001: (Severity.error, "Check the supplied input path."),
    PIPE_002: (Severity.error, "Choose a writable output directory."),
    PIPE_003: (Severity.error, "Choose a writable report path."),
    PIPE_004: (Severity.warning, "Check include and exclude patterns."),
    PIPE_005: (Severity.error, "Check permissions and disk space."),
    PIPE_006: (Severity.error, "Use a separate output directory."),
    PIPE_007: (Severity.error, "Adjust source roots or output policy."),
    PIPE_099: (Severity.error, "Re-run with logs and report the failure."),
}


def make_pipeline_diagnostic(
    code: str,
    message: str,
    detail: str = "",
) -> Diagnostic:
    """Create a pipeline-level Diagnostic with a PIPE-### code.

    :param code: PIPE-### error code string.
    :param message: Human-readable description.
    :param detail: Optional additional detail.
    :returns: A Diagnostic using the pipeline error namespace.
    """
    severity, remediation = _PIPE_META.get(code, (Severity.error, ""))
    return Diagnostic(
        code=code,
        severity=severity,
        category=DiagnosticCategory.internal_error,
        message=message,
        detail=detail,
        remediation=remediation,
    )


class PipelineFileStatus(StrEnum):
    """File-level pipeline processing status."""

    parsed = "parsed"
    parsed_with_warnings = "parsed_with_warnings"
    failed = "failed"
    skipped = "skipped"


class PipelineConfig(BaseModel):
    """Configuration for one folder-based pipeline run.

    :param inputs:
        Source files or folders selected by the caller.
    :param output_dir:
        Directory where parsed output files are written.
    :param report_path:
        Optional CSV inventory path. Defaults to
        ``output_dir / "pipeline-inventory.csv"``.
    :param parser_config:
        Existing parser configuration applied to every source file.
    """

    inputs: list[Path]
    output_dir: Path
    report_path: Path | None = None
    include_patterns: list[str] = Field(default_factory=lambda: ["*.md", "*.markdown"])
    exclude_patterns: list[str] = Field(default_factory=list)
    log_file: Path | None = None
    log_format: str = "text"
    strict: bool = False
    dry_run: bool = False
    parser_config: ParserConfig = Field(default_factory=ParserConfig)

    def effective_report_path(self) -> Path:
        """Return the report path, applying the default when none was provided.

        :returns: Caller-supplied report path or ``output_dir / pipeline-inventory.csv``.
        """
        return self.report_path or (self.output_dir / "pipeline-inventory.csv")


class DiscoveredSource(BaseModel):
    """One discovered source file ready for parsing."""

    source_root: Path
    source_path: Path
    relative_path: Path
    source_format: SourceFormat = SourceFormat.markdown


class PipelineFileResult(BaseModel):
    """Pipeline result for one source file."""

    source: DiscoveredSource
    target_path: Path | None = None
    status: PipelineFileStatus
    parser_codes: list[str] = Field(default_factory=list)
    pipeline_code: str | None = None
    error_count: int = 0
    warning_count: int = 0
    duration_ms: float = 0.0


class PipelineRunStats(BaseModel):
    """Aggregate statistics for one pipeline run."""

    discovered_count: int = 0
    parsed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    duration_ms: float = 0.0


class PipelineRunResult(BaseModel):
    """Complete result of one pipeline run."""

    schema_version: str = "1"
    run_id: str
    files: list[PipelineFileResult] = Field(default_factory=list)
    run_diagnostics: list[Diagnostic] = Field(default_factory=list)
    stats: PipelineRunStats = Field(default_factory=PipelineRunStats)
