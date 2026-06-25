"""Parser orchestrator — coordinates the full parse pipeline for one or more files."""
from __future__ import annotations
import logging
from pathlib import Path
from structure_parser.application.adapter_registry import get_adapter
from structure_parser.application.run_context import RunContext
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.diagnostics import DiagnosticFactory
from structure_parser.contracts.parse_run_result import ParseRunResult, ParseStats
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.domain.errors import (
    StructureParserError,
    SourceFileNotFoundError,
    UnsupportedFormatError,
)
from structure_parser.enrichment.semantic_enricher import enrich

_log = logging.getLogger("structure_parser.orchestrator")


def parse_one(path: Path, config: ParserConfig) -> ParsedDocument:
    """Parse a single source file through the full pipeline.

    :param path: Source file path.
    :param config: Parser configuration.
    :returns: A normalized ParsedDocument.
    """
    _log.debug("Parsing %s", path)

    try:
        adapter = get_adapter(path, config)
        raw = adapter.parse(path, config)
        doc = enrich(raw, config)
        _log.debug("Parsed %s → %d diagnostics", path, len(doc.diagnostics))
        return doc

    except SourceFileNotFoundError:
        from structure_parser.domain.enums import SourceFormat
        diag = DiagnosticFactory.source_file_not_found(str(path))
        return ParsedDocument(
            source_path=str(path),
            source_format=SourceFormat.unknown,
            diagnostics=[diag],
        )

    except UnsupportedFormatError:
        from structure_parser.domain.enums import SourceFormat
        diag = DiagnosticFactory.unsupported_format(path.suffix, source_path=str(path))
        return ParsedDocument(
            source_path=str(path),
            source_format=SourceFormat.unknown,
            diagnostics=[diag],
        )

    except StructureParserError as exc:
        from structure_parser.domain.enums import SourceFormat
        diag = DiagnosticFactory.internal_error(str(exc), source_path=str(path))
        return ParsedDocument(
            source_path=str(path),
            source_format=SourceFormat.unknown,
            diagnostics=[diag],
        )

    except Exception as exc:
        from structure_parser.domain.enums import SourceFormat
        _log.exception("Unexpected error parsing %s", path)
        diag = DiagnosticFactory.internal_error(str(exc), source_path=str(path))
        return ParsedDocument(
            source_path=str(path),
            source_format=SourceFormat.unknown,
            diagnostics=[diag],
        )


def parse_many(paths: list[Path], config: ParserConfig) -> ParseRunResult:
    """Parse multiple files and aggregate into a ParseRunResult.

    :param paths: List of source file paths.
    :param config: Parser configuration.
    :returns: A ParseRunResult with all documents and aggregate stats.
    """
    ctx = RunContext(config=config)
    documents = []

    for path in paths:
        doc = parse_one(path, config)
        documents.append(doc)

    error_count = sum(d.error_count for d in documents)
    warning_count = sum(d.warning_count for d in documents)

    stats = ParseStats(
        file_count=len(documents),
        error_count=error_count,
        warning_count=warning_count,
        duration_ms=ctx.elapsed_ms(),
    )

    return ParseRunResult(
        documents=documents,
        run_diagnostics=ctx.run_diagnostics,
        stats=stats,
    )
