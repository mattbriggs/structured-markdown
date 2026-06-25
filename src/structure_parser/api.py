"""Public API entry points for the structure parser."""
from __future__ import annotations
from pathlib import Path

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.parse_run_result import ParseRunResult, ParseStats
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.application.orchestrator import parse_one, parse_many
from structure_parser.logging_config import configure_logging


def parse_file(
    path: str | Path,
    config: ParserConfig | None = None,
) -> ParsedDocument:
    """Parse one source file into a normalized parser contract.

    :param path:
        Source file path selected by the caller. The path is treated as
        untrusted input and is loaded only through ``SourceRepository``.
    :param config:
        Optional parser configuration. When omitted, the default MVP
        configuration enables Markdown parsing, structured Markdown
        classification, advisory model validation, and no external
        resource resolution.
    :returns:
        A versioned ``ParsedDocument`` Pydantic contract. The result may
        contain diagnostics and partial structure when recoverable parse
        errors occur.
    :raises ParserConfigurationError:
        Raised when the requested schema version or adapter selection is
        unsupported.
    :side effects:
        Reads the source file and emits structured logs. Does not mutate
        the source file or execute source content.
    """
    cfg = config or ParserConfig()
    if cfg.emit_debug_logs:
        configure_logging(debug=True)
    return parse_one(Path(path), cfg)


def parse_files(
    paths: list[str | Path],
    config: ParserConfig | None = None,
) -> ParseRunResult:
    """Parse one or more source files into a ParseRunResult.

    :param paths:
        List of source file paths. Each path is treated as untrusted
        input and is loaded only through ``SourceRepository``.
    :param config:
        Optional parser configuration shared across all files.
    :returns:
        A ``ParseRunResult`` aggregating parsed documents, run-level
        diagnostics, and aggregate statistics.
    :side effects:
        Reads source files and emits structured logs.
    """
    cfg = config or ParserConfig()
    if cfg.emit_debug_logs:
        configure_logging(debug=True)
    return parse_many([Path(p) for p in paths], cfg)
