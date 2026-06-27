"""Structured Markdown classifier — maps raw nodes to the Article hierarchy."""
from __future__ import annotations

import hashlib
import re
from typing import Any

from structure_parser.contracts.diagnostics import Diagnostic, DiagnosticFactory
from structure_parser.contracts.raw import RawNode, RawParseModel
from structure_parser.contracts.structured_markdown import Component, StructuredContent, Unit
from structure_parser.domain.enums import (
    ArticleType,
    InformationType,
    ProcedureRepresentation,
    TriageStatus,
    UnitType,
)
from structure_parser.enrichment.provenance_mapper import node_to_span
from structure_parser.structured_markdown.component_mapper import map_block_node
from structure_parser.structured_markdown.unknowns import unknown_unit

# ---------------------------------------------------------------------------
# Heading keyword → UnitType
# ---------------------------------------------------------------------------
_UNIT_TITLE_MAP: dict[str, UnitType] = {
    "overview": UnitType.introduction,
    "introduction": UnitType.introduction,
    "before you begin": UnitType.prerequisites,
    "prerequisites": UnitType.prerequisites,
    "requirements": UnitType.prerequisites,
    "next steps": UnitType.link_nextstep,
    "next step": UnitType.link_nextstep,
    "related": UnitType.link_related,
    "related topics": UnitType.link_related,
    "see also": UnitType.link_related,
    "glossary": UnitType.glossary,
    "reference": UnitType.reference,
    "troubleshoot": UnitType.troubleshooting,
    "troubleshooting": UnitType.troubleshooting,
}

# Unit type → InformationType
_UNIT_INFO_TYPE: dict[UnitType, InformationType] = {
    UnitType.introduction: InformationType.concept,
    UnitType.concept: InformationType.concept,
    UnitType.procedure: InformationType.procedure,
    UnitType.principle: InformationType.principle,
    UnitType.process: InformationType.process,
    UnitType.fact: InformationType.fact,
    UnitType.reference: InformationType.fact,
    UnitType.troubleshooting: InformationType.process,
    UnitType.prerequisites: InformationType.concept,
    UnitType.link_nextstep: InformationType.concept,
    UnitType.link_related: InformationType.concept,
    UnitType.glossary: InformationType.fact,
    UnitType.glossentry: InformationType.fact,
    UnitType.unknown: InformationType.unknown,
}

# Metadata value → ArticleType
_ARTICLE_TYPE_MAP: dict[str, ArticleType] = {
    "topic": ArticleType.topic,
    "concept": ArticleType.concept,
    "howto": ArticleType.howto,
    "how-to": ArticleType.howto,
    "reference": ArticleType.reference,
    "troubleshooting": ArticleType.troubleshooting,
    "glossary": ArticleType.glossary,
    "glossentry": ArticleType.glossentry,
    "overview": ArticleType.overview,
    "quickstart": ArticleType.quickstart,
    "quick-start": ArticleType.quickstart,
    "tutorial": ArticleType.tutorial,
}

# ArticleType → DITA topic type string
_DITA_TYPE_MAP: dict[ArticleType, str] = {
    ArticleType.topic: "topic",
    ArticleType.concept: "concept",
    ArticleType.howto: "howto",
    ArticleType.reference: "reference",
    ArticleType.troubleshooting: "troubleshooting",
    ArticleType.glossary: "glossary",
    ArticleType.glossentry: "glossentry",
    ArticleType.overview: "topic",
    ArticleType.quickstart: "topic",
    ArticleType.tutorial: "topic",
    ArticleType.unknown: "topic",
}

# ArticleType → schema filename
_SCHEMA_MAP: dict[ArticleType, str] = {
    ArticleType.topic: "artTopic.schema.json",
    ArticleType.concept: "artConcept.schema.json",
    ArticleType.howto: "artHowto.schema.json",
    ArticleType.reference: "artReference.schema.json",
    ArticleType.troubleshooting: "artTroubleshooting.schema.json",
    ArticleType.glossary: "artGlossary.schema.json",
    ArticleType.glossentry: "artGlossentry.schema.json",
    ArticleType.overview: "artOverview.schema.json",
    ArticleType.quickstart: "artQuickstart.schema.json",
    ArticleType.tutorial: "artTutorial.schema.json",
    ArticleType.unknown: "artUnknown.schema.json",
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify(
    raw: RawParseModel,
    metadata: dict[str, Any],
) -> tuple[StructuredContent, list[Diagnostic]]:
    """Classify a RawParseModel into a StructuredContent article hierarchy.

    Args:
        raw: The raw parse model produced by a Markdown/HTML adapter.
        metadata: Front-matter key/value pairs extracted from the document.

    Returns:
        A (StructuredContent, diagnostics) tuple.
    """
    diags: list[Diagnostic] = []
    source_path = raw.source_path

    # Split nodes into H2 sections
    sections = _split_into_sections(raw.nodes)

    # Article-level metadata
    article_id = _make_id(source_path)
    title = metadata.get("title") or _find_h1_title(raw.nodes)

    # Determine article type
    article_type = _infer_article_type(metadata)
    if article_type == ArticleType.unknown:
        diags.append(DiagnosticFactory.unknown_article_type(source_path=source_path))

    # Build units from sections
    units: list[Unit] = []
    for section_nodes, section_heading in sections:
        unit, unit_diags = _build_unit(section_nodes, section_heading, metadata, source_path)
        units.append(unit)
        diags.extend(unit_diags)

    if not units:
        # Single unitless document — wrap everything as a single unknown unit
        all_comps = [
            map_block_node(n, source_path)
            for n in raw.nodes
            if not (n.node_type == "heading" and (n.level or 1) <= 1)
        ]
        if all_comps:
            units.append(unknown_unit(all_comps, title="Content"))
            diags.append(
                DiagnosticFactory.unknown_classification(
                    "Document has no H2 sections; content classified as single unknown unit.",
                    source_path=source_path,
                )
            )

    dita_type = _DITA_TYPE_MAP.get(article_type, "topic")
    info_type = _infer_article_info_type(units)
    triage = TriageStatus.known if article_type != ArticleType.unknown else TriageStatus.unknown
    schema_id = _SCHEMA_MAP.get(article_type, "artArticle.schema.json")

    source_dict: dict[str, Any] = {
        "sourcePath": source_path,
        "sourceFormat": raw.source_format.value,
    }
    if raw.content_hash:
        source_dict["contentHash"] = raw.content_hash

    content = StructuredContent(
        schema_name=schema_id,
        article_id=article_id,
        article_type=article_type,
        dita_type=dita_type,
        information_type=info_type,
        title=title,
        triage_status=triage,
        metadata=dict(metadata),
        source=source_dict,
        content=units,
    )
    return content, diags


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_into_sections(
    nodes: list[RawNode],
) -> list[tuple[list[RawNode], RawNode | None]]:
    """Split nodes into sections at H2 headings.

    Returns:
        A list of (body_nodes, heading_node) pairs. The heading_node is the H2
        that opened the section; it is None for any preamble before the first H2.
    """
    sections: list[tuple[list[RawNode], RawNode | None]] = []
    current_nodes: list[RawNode] = []
    current_heading: RawNode | None = None

    for node in nodes:
        if node.node_type == "heading" and (node.level or 1) == 2:
            if current_nodes or current_heading is not None:
                sections.append((current_nodes, current_heading))
            current_heading = node
            current_nodes = []
        elif node.node_type == "heading" and (node.level or 1) == 1:
            # H1 is the article title — skip it from section body content
            continue
        else:
            current_nodes.append(node)

    # Flush the last section
    if current_nodes or current_heading is not None:
        sections.append((current_nodes, current_heading))

    return sections


def _find_h1_title(nodes: list[RawNode]) -> str | None:
    for node in nodes:
        if node.node_type == "heading" and node.level == 1:
            return node.content or None
    return None


def _infer_article_type(metadata: dict[str, Any]) -> ArticleType:
    for key in ("articleType", "article_type", "type"):
        val = metadata.get(key)
        if val:
            mapped = _ARTICLE_TYPE_MAP.get(str(val).lower())
            if mapped is not None:
                return mapped
    return ArticleType.unknown


def _infer_unit_type(
    heading: RawNode | None,
    metadata: dict[str, Any],  # noqa: ARG001 — reserved for future metadata hints
) -> UnitType:
    """Infer unit type from the heading text keywords."""
    if heading:
        title_lower = (heading.content or "").lower().strip()
        for keyword, unit_type in _UNIT_TITLE_MAP.items():
            if keyword in title_lower:
                return unit_type

    # Check explicit metadata override
    unit_type_meta = metadata.get("unitType") or metadata.get("unit_type")
    if unit_type_meta:
        try:
            return UnitType(str(unit_type_meta))
        except ValueError:
            pass

    return UnitType.unknown


def _build_unit(
    nodes: list[RawNode],
    heading: RawNode | None,
    metadata: dict[str, Any],
    source_path: str,
) -> tuple[Unit, list[Diagnostic]]:
    diags: list[Diagnostic] = []

    unit_type = _infer_unit_type(heading, {})
    proc_repr: ProcedureRepresentation | None = None

    if unit_type == UnitType.unknown:
        # Heuristic: infer procedure from content shape
        has_ordered_list = any(n.node_type == "list" and n.tag == "ol" for n in nodes)
        has_code_block = any(n.node_type == "code_block" for n in nodes)
        has_paragraphs = any(n.node_type == "paragraph" for n in nodes)

        if has_ordered_list:
            unit_type = UnitType.procedure
            proc_repr = ProcedureRepresentation.ordered_list
        elif has_code_block and not has_paragraphs:
            unit_type = UnitType.procedure
            proc_repr = ProcedureRepresentation.code_block

    if unit_type == UnitType.unknown:
        diags.append(
            DiagnosticFactory.unknown_classification(
                detail=(
                    f"Unit '{heading.content if heading else 'unnamed'}' could not be classified."
                ),
                source_path=source_path,
                start_line=heading.start_line if heading else None,
            )
        )

    # Map all body block nodes to components
    components: list[Component] = [map_block_node(n, source_path) for n in nodes]

    info_type = _UNIT_INFO_TYPE.get(unit_type, InformationType.unknown)
    triage = TriageStatus.known if unit_type != UnitType.unknown else TriageStatus.unknown
    span = node_to_span(heading, source_path) if heading else None

    unit = Unit(
        unit_type=unit_type,
        unit_id=_make_id(heading.content if heading else "unit"),
        information_type=info_type,
        title=heading.content if heading else None,
        triage_status=triage,
        procedure_representation=proc_repr,
        source=span,
        content=components,
    )
    return unit, diags


def _infer_article_info_type(units: list[Unit]) -> InformationType:
    types = {u.information_type for u in units if u.information_type != InformationType.unknown}
    if not types:
        return InformationType.unknown
    if len(types) == 1:
        return next(iter(types))
    return InformationType.mixed


def _make_id(text: str) -> str:
    """Make a stable, URL-safe identifier from arbitrary text."""
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", text.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug or not slug[0].isalpha():
        slug = "doc-" + hashlib.sha256(text.encode()).hexdigest()[:8]
    return slug[:64]
