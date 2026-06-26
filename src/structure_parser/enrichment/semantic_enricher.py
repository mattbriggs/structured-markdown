"""Semantic enricher — converts a RawParseModel to a ParsedDocument."""
from __future__ import annotations

from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.provenance import DocumentProvenance
from structure_parser.contracts.raw import RawParseModel
from structure_parser.enrichment.metadata_extractor import extract_metadata
from structure_parser.enrichment.reference_classifier import classify_references
from structure_parser.enrichment.structure_builder import build_structure
from structure_parser.readiness.dita import DitaReadinessEvaluator
from structure_parser.readiness.evaluator import evaluate_readiness
from structure_parser.readiness.rag_ingestion import RagIngestionReadinessEvaluator
from structure_parser.readiness.schema_org import SchemaOrgReadinessEvaluator
from structure_parser.structured_markdown.classifier import classify
from structure_parser.validation.model_validator import validate_model


def enrich(raw: RawParseModel, config: ParserConfig) -> ParsedDocument:
    """Convert a RawParseModel into a fully enriched ParsedDocument.

    :param raw: The raw parse output from a format adapter.
    :param config: Parser configuration for this run.
    :returns: A normalized ParsedDocument with metadata, structure, references, and diagnostics.
    """
    all_diags: list[Diagnostic] = []

    # Handle any adapter-level parse errors
    for err in raw.parse_errors:
        all_diags.append(DiagnosticFactory.parse_failed(err, source_path=raw.source_path))

    # 1. Extract metadata
    metadata, meta_diags = extract_metadata(raw)
    all_diags.extend(meta_diags)

    # 2. Build structure
    structure, struct_diags = build_structure(raw)
    all_diags.extend(struct_diags)

    # 3. Classify references
    references = classify_references(raw)

    # 4. Optionally resolve local references
    if config.resolve_local_references:
        from structure_parser.resolution.local_file_resolver import resolve_references
        resolved, unresolved = resolve_references(references, raw.source_path)
        references = resolved + unresolved
        for ref in unresolved:
            all_diags.append(DiagnosticFactory.unresolved_reference(
                href=ref.href,
                source_path=ref.source_path,
                start_line=ref.start_line,
            ))

    # 5. Extract title
    title = metadata.get("title")
    if not title and structure.has_title:
        for node in raw.nodes:
            if node.node_type == "heading" and node.level == 1:
                title = node.content
                break

    # 6. Classify structured content (if enabled)
    structured_content = None
    if config.enable_structured_markdown:
        try:
            structured_content, class_diags = classify(raw, metadata)
            all_diags.extend(class_diags)
            if title and not structured_content.title:
                structured_content = structured_content.model_copy(update={"title": title})
        except Exception as exc:
            all_diags.append(DiagnosticFactory.internal_error(
                detail=f"Classification failed: {exc}",
                source_path=raw.source_path,
            ))

    # 7. Validate model (advisory or strict)
    validation_result = None
    if structured_content and config.enable_structured_markdown:
        try:
            profile = "default"
            if structured_content.article_type.value in ("howto", "concept", "reference"):
                profile = structured_content.article_type.value
            validation_result = validate_model(
                structured_content,
                profile_name=profile,
                model_dir=config.model_schema_dir,
            )
            if not validation_result.valid and config.validation_mode == "strict":
                all_diags.extend(validation_result.diagnostics)
            elif not validation_result.valid:
                # advisory: add as warnings only
                for d in validation_result.diagnostics[:5]:
                    all_diags.append(d)
        except Exception as exc:
            all_diags.append(DiagnosticFactory.internal_error(
                detail=f"Validation failed: {exc}",
                source_path=raw.source_path,
            ))

    # 8. Provenance
    provenance = DocumentProvenance(
        source_path=raw.source_path,
        source_format=raw.source_format,
        content_hash=raw.content_hash,
    )

    # Build document
    doc = ParsedDocument(
        source_path=raw.source_path,
        source_format=raw.source_format,
        provenance=provenance,
        metadata=metadata,
        title=title,
        structure=structure,
        structured_content=structured_content,
        references=references,
        diagnostics=all_diags[:config.max_diagnostic_count],
        validation=validation_result,
    )

    # 9. Evaluate transform readiness
    evaluators = [
        DitaReadinessEvaluator(),
        SchemaOrgReadinessEvaluator(),
        RagIngestionReadinessEvaluator(),
    ]
    readiness = evaluate_readiness(doc, evaluators)

    return doc.model_copy(update={"readiness": readiness})
