"""CLI command objects — unit-testable command implementations."""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from structure_parser.application.orchestrator import parse_many, parse_one
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.pipeline import PipelineConfig
from structure_parser.domain.enums import Severity
from structure_parser.validation.author_feedback import format_feedback
from structure_parser.validation.model_validator import validate_model


class ParseCommand:
    """Execute the `parse` CLI command."""

    def run(
        self,
        paths: list[Path],
        config: ParserConfig,
        json_output: bool = False,
        stdout: bool = True,
    ) -> tuple[str, int]:
        """Parse files and return (output_text, exit_code)."""
        result = parse_many(paths, config)

        if json_output:
            data = result.model_dump(mode="json", by_alias=True)
            text = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            lines = []
            lines.append(
                f"Parsed {result.stats.file_count} file(s) in {result.stats.duration_ms:.0f}ms"
            )
            lines.append(
                f"  Errors: {result.stats.error_count}  Warnings: {result.stats.warning_count}"
            )
            for doc in result.documents:
                lines.append(f"  {doc.source_path}")
                if doc.title:
                    lines.append(f"    Title: {doc.title}")
                if doc.structured_content:
                    lines.append(
                        f"    Article type: {doc.structured_content.article_type.value}"
                    )
                    lines.append(f"    Units: {len(doc.structured_content.content)}")
                if doc.diagnostics:
                    lines.append(f"    Diagnostics: {len(doc.diagnostics)}")
            text = "\n".join(lines)

        exit_code = 0 if not result.stats.error_count else 1
        return text, exit_code


class ValidateMarkdownCommand:
    """Execute the `validate-markdown` CLI command."""

    def run(
        self,
        paths: list[Path],
        schema_id: str,
        config: ParserConfig,
        strict: bool = False,
    ) -> tuple[str, int]:
        """Validate Markdown files and return (output_text, exit_code)."""
        lines = []
        has_invalid = False

        for path in paths:
            doc = parse_one(path, config)
            if doc.structured_content:
                result = validate_model(
                    doc.structured_content,
                    profile_name="default",
                    model_dir=config.model_schema_dir,
                    timeout_seconds=config.schema_validation_timeout_seconds,
                )
                status = "VALID" if result.valid else "INVALID"
                lines.append(f"{path}: {status}")
                if not result.valid:
                    has_invalid = True
                    lines.append(format_feedback(result.diagnostics, source_path=str(path)))
            else:
                lines.append(f"{path}: SKIPPED (no structured content)")

        exit_code = 1 if (has_invalid and strict) else 0
        return "\n".join(lines), exit_code


class InspectStructureCommand:
    """Execute the `inspect-structure` CLI command."""

    def run(self, path: Path, config: ParserConfig) -> tuple[str, int]:
        doc = parse_one(path, config)
        if not doc.structure:
            return f"{path}: No structure available", 1

        lines = [f"Structure: {path}"]
        lines.append(f"  Title: {doc.title or '(none)'}")
        lines.append(f"  Headings: {doc.structure.heading_count}")
        lines.append(f"  Max depth: {doc.structure.max_depth}")
        lines.append("")
        _render_node(doc.structure.root, lines, indent=0)
        return "\n".join(lines), 0


def _render_node(node: object, lines: list, indent: int) -> None:
    from structure_parser.contracts.structure import StructuralNode
    if not isinstance(node, StructuralNode):
        return
    prefix = "  " * indent
    label = node.title or node.node_type
    lines.append(f"{prefix}{node.path}: {label}")
    for child in node.children:
        _render_node(child, lines, indent + 1)


class InspectModelCommand:
    """Execute the `inspect-model` CLI command."""

    def run(self, path: Path, config: ParserConfig) -> tuple[str, int]:
        doc = parse_one(path, config)
        if not doc.structured_content:
            return f"{path}: No structured content available", 1

        sc = doc.structured_content
        lines = [f"Model: {path}"]
        lines.append(f"  Article type: {sc.article_type.value}")
        lines.append(f"  Information type: {sc.information_type.value}")
        lines.append(f"  Triage status: {sc.triage_status.value}")
        lines.append(f"  Units: {len(sc.content)}")
        for i, unit in enumerate(sc.content):
            lines.append(f"    [{i}] {unit.unit_type.value}: {unit.title or '(untitled)'}")
            lines.append(f"        Components: {len(unit.content)}")
        return "\n".join(lines), 0


class InspectReferencesCommand:
    """Execute the `inspect-references` CLI command."""

    def run(self, path: Path, config: ParserConfig) -> tuple[str, int]:
        doc = parse_one(path, config)
        lines = [f"References: {path}"]
        if not doc.references:
            lines.append("  No references found.")
        for ref in doc.references:
            loc = f":{ref.start_line}" if ref.start_line else ""
            lines.append(f"  [{ref.ref_type}] {ref.href} ({ref.state.value}){loc}")
        return "\n".join(lines), 0


class InspectDiagnosticsCommand:
    """Execute the `inspect-diagnostics` CLI command."""

    def run(self, path: Path, config: ParserConfig) -> tuple[str, int]:
        doc = parse_one(path, config)
        text = format_feedback(doc.diagnostics, source_path=str(path))
        exit_code = 1 if doc.has_errors else 0
        return text, exit_code


class TransformReadinessCommand:
    """Execute the `transform-readiness` CLI command."""

    def run(
        self,
        path: Path,
        config: ParserConfig,
        targets: list[str] | None = None,
    ) -> tuple[str, int]:
        doc = parse_one(path, config)
        lines = [f"Transform readiness: {path}"]

        if not doc.readiness:
            lines.append("  Readiness not evaluated.")
            return "\n".join(lines), 0

        has_blocked = False
        for t in doc.readiness.targets:
            if targets and t.target not in targets:
                continue
            lines.append(f"\n  Target: {t.target}")
            lines.append(f"  Status: {t.status.value.upper()}")
            if t.prerequisites_met:
                lines.append("  Met:")
                for p in t.prerequisites_met:
                    lines.append(f"    + {p}")
            if t.prerequisites_missing:
                lines.append("  Missing:")
                for p in t.prerequisites_missing:
                    lines.append(f"    - {p}")
                if t.status.value == "blocked":
                    has_blocked = True

        exit_code = 1 if has_blocked else 0
        return "\n".join(lines), exit_code


class PipelineCommand:
    """Execute the ``pipe`` CLI command."""

    def run(
        self,
        config: PipelineConfig,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> tuple[str, int]:
        """Run the pipeline and return (summary_text, exit_code).

        :param config: Pipeline configuration.
        :returns:
            A tuple of human-readable summary text and a CLI exit code.
            Exit code is 0 on success, 1 when errors or failures are present,
            and 1 in strict mode when warnings are present.
        :side effects:
            Runs the pipeline orchestrator, writes parsed outputs, writes the
            CSV inventory report, and optionally adds a log file handler.
        """
        from structure_parser.pipeline.orchestrator import PipelineOrchestrator
        from structure_parser.pipeline.reporting import CsvInventoryReporter

        log_handler = _add_log_file_handler(config) if config.log_file else None
        try:
            result = PipelineOrchestrator().run(config, progress_callback=progress_callback)
            report_path = config.effective_report_path()
            CsvInventoryReporter().write(result, report_path)
            _log_report_written(report_path)

            stats = result.stats
            lines = [
                f"Pipeline parsed {stats.discovered_count} Markdown file(s)"
                f" in {stats.duration_ms:.0f}ms"
            ]
            lines.append(
                f"  Parsed: {stats.parsed_count}"
                f"  Failed: {stats.failed_count}"
                f"  Skipped: {stats.skipped_count}"
            )
            lines.append(f"  Errors: {stats.error_count}  Warnings: {stats.warning_count}")
            lines.append(f"  Output: {config.output_dir}")
            lines.append(f"  Report: {report_path}")
            if config.log_file:
                lines.append(f"  Log: {config.log_file}")

            has_run_errors = any(d.severity == Severity.error for d in result.run_diagnostics)
            has_errors = stats.error_count > 0 or stats.failed_count > 0 or has_run_errors
            has_warnings = stats.warning_count > 0

            exit_code = 1 if has_errors or (config.strict and has_warnings) else 0

            return "\n".join(lines), exit_code
        finally:
            if log_handler:
                logging.getLogger("structure_parser").removeHandler(log_handler)
                log_handler.close()


def _add_log_file_handler(config: PipelineConfig) -> logging.Handler:
    """Add a file handler to the structure_parser logger for the pipeline run.

    :param config: Pipeline configuration with log_file and log_format.
    :returns: The added handler (caller must remove it when the run finishes).
    :side effects: Creates parent directories, opens a log file, adds a handler.
    """
    assert config.log_file is not None
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    handler: logging.Handler = logging.FileHandler(str(config.log_file), encoding="utf-8")
    if config.log_format == "jsonl":
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore[import]

            handler.setFormatter(jsonlogger.JsonFormatter())
        except ImportError:
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
            )
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
    sp_logger = logging.getLogger("structure_parser")
    # Ensure the logger emits at least INFO when no prior configuration has run.
    if sp_logger.level == logging.NOTSET:
        sp_logger.setLevel(logging.INFO)
    sp_logger.addHandler(handler)
    return handler


def _log_report_written(report_path: Path) -> None:
    logging.getLogger("structure_parser.pipeline").info(
        "pipeline.report.written", extra={"report_path": str(report_path)}
    )


class ValidateContractCommand:
    """Execute the `validate-contract` CLI command."""

    def run(self, fixture_paths: list[Path], config: ParserConfig) -> tuple[str, int]:
        lines = []
        all_pass = True

        for path in fixture_paths:
            doc = parse_one(path, config)
            status = "PASS" if not doc.has_errors else "FAIL"
            if doc.has_errors:
                all_pass = False
            lines.append(f"{status}: {path.name}")
            for d in doc.diagnostics:
                if d.severity.value in ("error",):
                    lines.append(f"  [{d.code}] {d.message}")

        summary = (
            "All contract checks passed."
            if all_pass
            else "Some contract checks failed."
        )
        lines.append(f"\n{summary}")
        return "\n".join(lines), 0 if all_pass else 1
