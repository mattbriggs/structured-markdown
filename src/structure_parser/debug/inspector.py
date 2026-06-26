"""Debug inspector — human-readable views of parsed document internals."""
from __future__ import annotations

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.reporting.diagnostic_reporter import report_diagnostics
from structure_parser.reporting.readiness_reporter import report_readiness
from structure_parser.reporting.reference_reporter import report_references
from structure_parser.reporting.structure_reporter import report_structure


def inspect_document(doc: ParsedDocument) -> str:
    """Full debug inspection of a ParsedDocument."""
    sections: list[str] = []

    # Header
    sections.append(f"=== Debug Inspection: {doc.source_path} ===")
    sections.append(f"Format: {doc.source_format.value}")
    sections.append(f"Title: {doc.title or '(none)'}")
    sections.append(f"Schema version: {doc.schema_version}")
    sections.append("")

    # Metadata
    if doc.metadata:
        sections.append("--- Metadata ---")
        for k, v in doc.metadata.items():
            sections.append(f"  {k}: {v}")
        sections.append("")

    # Structure
    if doc.structure:
        sections.append("--- Structure ---")
        sections.append(report_structure(doc.structure))
        sections.append("")

    # Structured content
    if doc.structured_content:
        sc = doc.structured_content
        sections.append("--- Structured Content ---")
        sections.append(f"  Article type: {sc.article_type.value}")
        sections.append(f"  Information type: {sc.information_type.value}")
        sections.append(f"  Triage: {sc.triage_status.value}")
        sections.append(f"  Units ({len(sc.content)}):")
        for i, unit in enumerate(sc.content):
            sections.append(f"    [{i}] {unit.unit_type.value}: {unit.title or '(untitled)'}")
            sections.append(
                f"        Info type: {unit.information_type.value}"
                f"  Triage: {unit.triage_status.value}"
            )
            sections.append(f"        Components: {len(unit.content)}")
        sections.append("")

    # References
    if doc.references:
        sections.append("--- References ---")
        sections.append(report_references(doc.references))
        sections.append("")

    # Diagnostics
    if doc.diagnostics:
        sections.append("--- Diagnostics ---")
        sections.append(report_diagnostics(doc.diagnostics, source_path=doc.source_path))
        sections.append("")

    # Validation
    if doc.validation:
        sections.append("--- Validation ---")
        sections.append(f"  Valid: {doc.validation.valid}")
        sections.append(f"  Schema: {doc.validation.schema_id}")
        if doc.validation.diagnostics:
            for d in doc.validation.diagnostics:
                sections.append(f"  [{d.code}] {d.message}")
        sections.append("")

    # Readiness
    if doc.readiness:
        sections.append("--- Readiness ---")
        sections.append(report_readiness(doc.readiness))
        sections.append("")

    return "\n".join(sections)
