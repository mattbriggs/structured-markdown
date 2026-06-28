"""Pipeline orchestrator: coordinates discovery, parsing, writing, and reporting."""
from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from structure_parser.application.orchestrator import parse_one
from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.pipeline import (
    PIPE_006,
    PIPE_007,
    PIPE_099,
    DiscoveredSource,
    PipelineConfig,
    PipelineFileResult,
    PipelineFileStatus,
    PipelineRunResult,
    PipelineRunStats,
    make_pipeline_diagnostic,
)
from structure_parser.domain.enums import Severity
from structure_parser.pipeline.discovery import MarkdownDiscoveryService
from structure_parser.pipeline.output import ParsedDocumentWriter

_log = logging.getLogger("structure_parser.pipeline.orchestrator")


class PipelineOrchestrator:
    """End-to-end pipeline coordinator.

    Wraps discovery, per-file parsing, output writing, and statistics
    aggregation without implementing Markdown parsing or content semantics.
    """

    def run(self, config: PipelineConfig) -> PipelineRunResult:
        """Run the complete pipeline and return a result.

        :param config: Pipeline configuration.
        :returns:
            Aggregated PipelineRunResult containing per-file results, run-level
            diagnostics, and aggregate statistics.
        :side effects:
            Discovers files, calls the parser for each file, writes parsed
            outputs to disk (unless dry_run), and logs events throughout.
        """
        run_id = uuid.uuid4().hex
        run_start = time.perf_counter()

        _log.info("pipeline.start", extra={"run_id": run_id, "dry_run": config.dry_run})

        writer = ParsedDocumentWriter()
        run_diags: list[Diagnostic] = []

        # Fail fast on unsafe source/output overlap (PIPE-006)
        if writer.check_overlap(config.inputs, config.output_dir):
            run_diags.append(
                make_pipeline_diagnostic(
                    PIPE_006,
                    "Source and output roots overlap unsafely.",
                    detail=str(config.output_dir),
                )
            )
            return _make_run_result(run_id, [], run_diags, run_start)

        # Discover source files
        discovery_svc = MarkdownDiscoveryService()
        sources, discovery_diags = discovery_svc.discover(config)
        run_diags.extend(discovery_diags)

        if not sources:
            return _make_run_result(run_id, [], run_diags, run_start)

        # Fail fast on duplicate target paths (PIPE-007)
        duplicates = writer.check_duplicate_targets(sources, config.output_dir)
        if duplicates:
            run_diags.append(
                make_pipeline_diagnostic(
                    PIPE_007,
                    f"Duplicate relative target paths detected: {duplicates}",
                    detail="; ".join(duplicates),
                )
            )
            return _make_run_result(run_id, [], run_diags, run_start)

        # Process each file independently
        file_results: list[PipelineFileResult] = []
        for source in sources:
            result = _process_one(source, config, writer, run_id)
            file_results.append(result)

        stats = _build_stats(file_results, time.perf_counter() - run_start)

        _log.info(
            "pipeline.complete",
            extra={
                "run_id": run_id,
                "parsed": stats.parsed_count,
                "failed": stats.failed_count,
                "duration_ms": f"{stats.duration_ms:.0f}",
            },
        )

        return PipelineRunResult(
            run_id=run_id,
            files=file_results,
            run_diagnostics=run_diags,
            stats=stats,
        )


def _process_one(
    source: DiscoveredSource,
    config: PipelineConfig,
    writer: ParsedDocumentWriter,
    run_id: str,
) -> PipelineFileResult:
    """Parse and write one source file, returning a file-level result.

    :param source: Discovered source to process.
    :param config: Pipeline configuration.
    :param writer: Document writer instance.
    :param run_id: Current run identifier (for log context).
    :returns: PipelineFileResult regardless of success or failure.
    :side effects: Calls the parser and writes output to disk.
    """
    file_start = time.perf_counter()
    target_path = writer.target_for(source, config.output_dir)
    rel = source.relative_path.as_posix()

    _log.debug("pipeline.file.start", extra={"run_id": run_id, "relative_path": rel})

    try:
        doc = parse_one(source.source_path, config.parser_config)

        _log.debug(
            "pipeline.file.parsed",
            extra={"run_id": run_id, "relative_path": rel, "errors": doc.error_count},
        )

        parser_codes = [d.code for d in doc.diagnostics]

        write_error = writer.write(doc, target_path, dry_run=config.dry_run)

        elapsed = (time.perf_counter() - file_start) * 1000

        if write_error:
            _log.warning("pipeline.file.failed", extra={"run_id": run_id, "relative_path": rel})
            return PipelineFileResult(
                source=source,
                target_path=target_path,
                status=PipelineFileStatus.failed,
                parser_codes=parser_codes,
                pipeline_code=write_error,
                error_count=doc.error_count,
                warning_count=doc.warning_count,
                duration_ms=elapsed,
            )

        if not config.dry_run:
            _log.debug(
                "pipeline.file.written", extra={"run_id": run_id, "relative_path": rel}
            )

        if doc.has_errors:
            status = PipelineFileStatus.failed
            _log.warning("pipeline.file.failed", extra={"run_id": run_id, "relative_path": rel})
        elif doc.warning_count > 0:
            status = PipelineFileStatus.parsed_with_warnings
        else:
            status = PipelineFileStatus.parsed

        return PipelineFileResult(
            source=source,
            target_path=target_path,
            status=status,
            parser_codes=parser_codes,
            pipeline_code=None,
            error_count=doc.error_count,
            warning_count=doc.warning_count,
            duration_ms=elapsed,
        )

    except Exception as exc:
        elapsed = (time.perf_counter() - file_start) * 1000
        _log.exception("pipeline.file.failed", extra={"run_id": run_id, "relative_path": rel})
        return PipelineFileResult(
            source=source,
            target_path=target_path,
            status=PipelineFileStatus.failed,
            parser_codes=[],
            pipeline_code=f"{PIPE_099}: {exc}",
            error_count=1,
            warning_count=0,
            duration_ms=elapsed,
        )


def _make_run_result(
    run_id: str,
    files: list[PipelineFileResult],
    run_diags: list[Diagnostic],
    run_start: float,
) -> PipelineRunResult:
    stats = _build_stats(files, time.perf_counter() - run_start)
    has_run_errors = any(d.severity == Severity.error for d in run_diags)
    if has_run_errors:
        stats = PipelineRunStats(
            discovered_count=len(files),
            failed_count=len(files),
            duration_ms=(time.perf_counter() - run_start) * 1000,
        )
    return PipelineRunResult(
        run_id=run_id,
        files=files,
        run_diagnostics=run_diags,
        stats=stats,
    )


def _build_stats(file_results: list[PipelineFileResult], elapsed_s: float) -> PipelineRunStats:
    parsed = sum(
        1
        for r in file_results
        if r.status in (PipelineFileStatus.parsed, PipelineFileStatus.parsed_with_warnings)
    )
    failed = sum(1 for r in file_results if r.status == PipelineFileStatus.failed)
    skipped = sum(1 for r in file_results if r.status == PipelineFileStatus.skipped)
    errors = sum(r.error_count for r in file_results)
    warnings = sum(r.warning_count for r in file_results)
    return PipelineRunStats(
        discovered_count=len(file_results),
        parsed_count=parsed,
        failed_count=failed,
        skipped_count=skipped,
        error_count=errors,
        warning_count=warnings,
        duration_ms=elapsed_s * 1000,
    )


def _resolve_output_dir(output_dir: Path) -> Path:
    return output_dir.resolve()
