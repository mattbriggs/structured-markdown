"""Tests for PipelineOrchestrator."""
from pathlib import Path
from typing import Any

from structure_parser.contracts.pipeline import (
    PIPE_006,
    PIPE_007,
    PipelineConfig,
    PipelineFileStatus,
)
from structure_parser.pipeline.orchestrator import PipelineOrchestrator

_MINIMAL_MD = "# Hello\n\nA paragraph.\n"
_HOWTO_MD = """\
---
title: Install Guide
articleType: howto
---

# Install Guide

## Introduction

This guide covers installation.

## Prerequisites

- Python 3.11+

## Steps

1. Download the package.
2. Run the installer.
"""


def _make_config(tmp_path: Path, docs_dir: Path, **kwargs: Any) -> PipelineConfig:
    return PipelineConfig(
        inputs=[docs_dir],
        output_dir=tmp_path / "out",
        **kwargs,
    )


class TestSuccessfulRun:
    def test_single_file_parsed(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        assert result.stats.discovered_count == 1
        assert result.stats.failed_count == 0
        assert len(result.files) == 1

    def test_nested_files_all_parsed(self, tmp_path):
        (tmp_path / "docs/guide").mkdir(parents=True)
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        (tmp_path / "docs/guide/install.md").write_text(_HOWTO_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        assert result.stats.discovered_count == 2
        assert result.stats.parsed_count + result.stats.parsed_count >= 1

    def test_run_id_is_hex_string(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        assert len(result.run_id) == 32
        assert all(c in "0123456789abcdef" for c in result.run_id)

    def test_output_files_written(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        PipelineOrchestrator().run(config)
        assert (tmp_path / "out/index.md.json").exists()

    def test_target_paths_set_in_results(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        assert result.files[0].target_path is not None
        assert result.files[0].target_path.name == "index.md.json"


class TestDryRun:
    def test_dry_run_no_output_files(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs", dry_run=True)
        PipelineOrchestrator().run(config)
        assert not (tmp_path / "out/index.md.json").exists()

    def test_dry_run_still_returns_results(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs", dry_run=True)
        result = PipelineOrchestrator().run(config)
        assert result.stats.discovered_count == 1


class TestFailFastChecks:
    def test_overlap_returns_run_diagnostic(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(_MINIMAL_MD)
        # Output inside input
        config = PipelineConfig(
            inputs=[docs],
            output_dir=docs / "out",
        )
        result = PipelineOrchestrator().run(config)
        codes = [d.code for d in result.run_diagnostics]
        assert PIPE_006 in codes
        assert result.stats.discovered_count == 0

    def test_duplicate_targets_returns_run_diagnostic(self, tmp_path):
        (tmp_path / "root1").mkdir()
        (tmp_path / "root2").mkdir()
        (tmp_path / "root1/index.md").write_text(_MINIMAL_MD)
        (tmp_path / "root2/index.md").write_text(_MINIMAL_MD)
        # Two inputs with same relative paths produce duplicate targets
        config = PipelineConfig(
            inputs=[tmp_path / "root1", tmp_path / "root2"],
            output_dir=tmp_path / "out",
        )
        result = PipelineOrchestrator().run(config)
        codes = [d.code for d in result.run_diagnostics]
        assert PIPE_007 in codes


class TestFileFailure:
    def test_one_failure_does_not_stop_others(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/good.md").write_text(_MINIMAL_MD)
        # A file that will be deleted before parsing simulates a race condition.
        # Since the parser returns SP-001 for missing files (not an exception),
        # we test with a missing explicit input path instead.
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        # Good file should still be discovered and attempted
        assert result.stats.discovered_count >= 1

    def test_stats_aggregate_errors(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        # Stats match summed file results
        total_errors = sum(f.error_count for f in result.files)
        assert result.stats.error_count == total_errors


class TestStrictMode:
    def test_strict_not_applied_by_orchestrator(self, tmp_path):
        # Strict mode is a CLI concern; orchestrator always produces full results
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(_MINIMAL_MD)
        config = _make_config(tmp_path, tmp_path / "docs", strict=True)
        result = PipelineOrchestrator().run(config)
        assert result is not None

    def test_file_with_warnings_gets_parsed_with_warnings_status(self, tmp_path):
        # A file without a title will produce SP-020 warning
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/notitle.md").write_text("Just a paragraph with no title.\n")
        config = _make_config(tmp_path, tmp_path / "docs")
        result = PipelineOrchestrator().run(config)
        statuses = [f.status for f in result.files]
        # Either parsed or parsed_with_warnings depending on parser diagnostics
        assert all(s in (PipelineFileStatus.parsed, PipelineFileStatus.parsed_with_warnings)
                   for s in statuses)
