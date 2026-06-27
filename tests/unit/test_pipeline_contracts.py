"""Tests for pipeline Pydantic contracts."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from structure_parser.contracts.pipeline import (
    DiscoveredSource,
    PipelineConfig,
    PipelineFileResult,
    PipelineFileStatus,
    PipelineRunResult,
    PipelineRunStats,
)
from structure_parser.domain.enums import SourceFormat


class TestPipelineConfig:
    def test_defaults(self):
        cfg = PipelineConfig(inputs=[Path("docs")], output_dir=Path("out"))
        assert cfg.include_patterns == ["*.md", "*.markdown"]
        assert cfg.exclude_patterns == []
        assert cfg.dry_run is False
        assert cfg.strict is False
        assert cfg.log_file is None
        assert cfg.log_format == "text"

    def test_effective_report_path_default(self):
        cfg = PipelineConfig(inputs=[Path("docs")], output_dir=Path("out"))
        assert cfg.effective_report_path() == Path("out/pipeline-inventory.csv")

    def test_effective_report_path_custom(self):
        cfg = PipelineConfig(
            inputs=[Path("docs")],
            output_dir=Path("out"),
            report_path=Path("custom.csv"),
        )
        assert cfg.effective_report_path() == Path("custom.csv")

    def test_inputs_required(self):
        with pytest.raises(ValidationError):
            PipelineConfig(output_dir=Path("out"))  # type: ignore[call-arg]

    def test_output_dir_required(self):
        with pytest.raises(ValidationError):
            PipelineConfig(inputs=[Path("docs")])  # type: ignore[call-arg]


class TestPipelineFileStatus:
    def test_str_values(self):
        assert PipelineFileStatus.parsed == "parsed"
        assert PipelineFileStatus.parsed_with_warnings == "parsed_with_warnings"
        assert PipelineFileStatus.failed == "failed"
        assert PipelineFileStatus.skipped == "skipped"

    def test_serializes_as_string(self):
        assert str(PipelineFileStatus.parsed) == "parsed"


class TestDiscoveredSource:
    def test_defaults_to_markdown(self):
        src = DiscoveredSource(
            source_root=Path("/docs"),
            source_path=Path("/docs/index.md"),
            relative_path=Path("index.md"),
        )
        assert src.source_format == SourceFormat.markdown

    def test_fields_preserved(self):
        src = DiscoveredSource(
            source_root=Path("/docs"),
            source_path=Path("/docs/guide/install.md"),
            relative_path=Path("guide/install.md"),
        )
        assert src.relative_path == Path("guide/install.md")
        assert src.source_root == Path("/docs")


class TestPipelineFileResult:
    def test_defaults(self):
        src = DiscoveredSource(
            source_root=Path("/docs"),
            source_path=Path("/docs/index.md"),
            relative_path=Path("index.md"),
        )
        result = PipelineFileResult(source=src, status=PipelineFileStatus.parsed)
        assert result.parser_codes == []
        assert result.pipeline_code is None
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.duration_ms == 0.0


class TestPipelineRunStats:
    def test_all_defaults_zero(self):
        stats = PipelineRunStats()
        assert stats.discovered_count == 0
        assert stats.parsed_count == 0
        assert stats.failed_count == 0
        assert stats.skipped_count == 0
        assert stats.error_count == 0
        assert stats.warning_count == 0
        assert stats.duration_ms == 0.0


class TestPipelineRunResult:
    def test_schema_version_default(self):
        result = PipelineRunResult(run_id="abc123")
        assert result.schema_version == "1"
        assert result.files == []
        assert result.run_diagnostics == []

    def test_run_id_preserved(self):
        result = PipelineRunResult(run_id="deadbeef")
        assert result.run_id == "deadbeef"
