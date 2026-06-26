"""Metadata extractor — extracts and normalizes front matter and metadata hooks."""
from __future__ import annotations

from typing import Any

from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.contracts.raw import RawParseModel


def extract_metadata(raw: RawParseModel) -> tuple[dict[str, Any], list[Diagnostic]]:
    """Extract and validate metadata from a RawParseModel's front matter.

    Returns a normalized metadata dict and any diagnostics about the metadata quality.
    """
    diags: list[Diagnostic] = []
    metadata: dict[str, Any] = {}

    if raw.front_matter_error:
        diags.append(DiagnosticFactory.malformed_front_matter(
            detail=raw.front_matter_error,
            source_path=raw.source_path,
            start_line=1,
        ))
    elif not raw.front_matter:
        diags.append(DiagnosticFactory.front_matter_absent(source_path=raw.source_path))
    else:
        metadata = dict(raw.front_matter)

    return metadata, diags
