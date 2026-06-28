"""Structured Markdown classifier — maps raw nodes to the Article hierarchy."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
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
# Evidence models
# ---------------------------------------------------------------------------

@dataclass
class _MetadataEvidence:
    """Evidence contributed by front-matter metadata."""
    candidate_type: ArticleType
    weight: int  # 10 = authoritative, 6 = secondary-exact, 4 = suffix-matched


@dataclass
class _ArticleCandidateScore:
    """Score accumulated for one article type candidate."""
    article_type: ArticleType
    score: int
    required_met: bool
    supporting_units: list[UnitType] = field(default_factory=list)
    conflicting_units: list[UnitType] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Heading keyword → UnitType
# ---------------------------------------------------------------------------
_UNIT_TITLE_MAP: dict[str, UnitType] = {
    # Longer / more-specific patterns must appear before shorter ones so the
    # substring match picks the most precise classification first.
    "before creating": UnitType.concept,
    "before you begin": UnitType.prerequisites,
    "what is": UnitType.concept,
    "how to": UnitType.procedure,
    "how it works": UnitType.process,
    "best practices": UnitType.principle,
    "best practice": UnitType.principle,
    "design considerations": UnitType.principle,
    "related topics": UnitType.link_related,
    "next steps": UnitType.link_nextstep,
    "next step": UnitType.link_nextstep,
    "cheat sheet": UnitType.reference,
    "api version": UnitType.reference,
    "release notes": UnitType.reference,
    # Single-word / short patterns
    "overview": UnitType.introduction,
    "introduction": UnitType.introduction,
    "about": UnitType.concept,
    "background": UnitType.concept,
    "concept": UnitType.concept,
    "understand": UnitType.concept,
    "architecture": UnitType.concept,
    "prerequisites": UnitType.prerequisites,
    "requirements": UnitType.prerequisites,
    "steps": UnitType.procedure,
    "procedure": UnitType.procedure,
    "process": UnitType.process,
    "lifecycle": UnitType.principle,
    "principles": UnitType.principle,
    "principle": UnitType.principle,
    "guidelines": UnitType.principle,
    "considerations": UnitType.principle,
    "rules": UnitType.principle,
    "facts": UnitType.fact,
    "parameters": UnitType.reference,
    "options": UnitType.reference,
    "configuration": UnitType.reference,
    "settings": UnitType.reference,
    "limits": UnitType.reference,
    "limitations": UnitType.reference,
    "matrix": UnitType.reference,
    "comparison": UnitType.reference,
    "differences": UnitType.reference,
    "versions": UnitType.reference,
    "reference": UnitType.reference,
    "related": UnitType.link_related,
    "see also": UnitType.link_related,
    "glossary": UnitType.glossary,
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

# Metadata value → ArticleType (shared by all metadata key lookups)
_ARTICLE_TYPE_MAP: dict[str, ArticleType] = {
    "topic": ArticleType.topic,
    "concept": ArticleType.concept,
    "conceptual": ArticleType.concept,
    "overview": ArticleType.overview,
    "howto": ArticleType.howto,
    "how-to": ArticleType.howto,
    "task": ArticleType.howto,
    "procedure": ArticleType.howto,
    "reference": ArticleType.reference,
    "api": ArticleType.reference,
    "schema": ArticleType.reference,
    "configuration": ArticleType.reference,
    "troubleshooting": ArticleType.troubleshooting,
    "glossary": ArticleType.glossary,
    "glossentry": ArticleType.glossentry,
    "quickstart": ArticleType.quickstart,
    "quick-start": ArticleType.quickstart,
    "tutorial": ArticleType.tutorial,
    "guide": ArticleType.topic,
    "article": ArticleType.topic,
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
# Metadata key classification
# ---------------------------------------------------------------------------

# Keys whose values are treated as direct author declarations (weight 10).
_AUTHORITATIVE_METADATA_KEYS: frozenset[str] = frozenset({"articleType", "article_type"})

# Additional exact keys whose values are treated as secondary evidence (weight 6).
_SECONDARY_EXACT_KEYS: frozenset[str] = frozenset({
    "type", "topic", "topic_type", "content_type", "document_type", "information_type",
})

# Suffix patterns for namespaced keys such as "ms.topic", "vendor.content_type" (weight 4).
_METADATA_SUFFIX_PATTERNS: tuple[str, ...] = (".topic", ".type", ".content_type")


# ---------------------------------------------------------------------------
# Article triage signatures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArticleSignature:
    """Evidence-based triage signature for one article type."""

    required_any: frozenset[UnitType]
    supporting: frozenset[UnitType] = frozenset()
    neutral: frozenset[UnitType] = frozenset()
    conflicting: frozenset[UnitType] = frozenset()
    excluded: frozenset[UnitType] = frozenset()
    required_weight: int = 5
    supporting_weight: int = 2
    neutral_weight: int = 0
    conflict_weight: int = -3
    min_score: int = 5


_ARTICLE_SIGNATURES: dict[ArticleType, ArticleSignature] = {
    ArticleType.howto: ArticleSignature(
        required_any=frozenset({UnitType.procedure}),
        supporting=frozenset({UnitType.prerequisites, UnitType.introduction}),
        # link_nextstep is navigation, not procedure evidence — keep neutral
        neutral=frozenset({UnitType.link_nextstep, UnitType.link_related}),
        conflicting=frozenset({UnitType.concept, UnitType.reference, UnitType.fact, UnitType.principle}),
        excluded=frozenset({UnitType.glossary, UnitType.glossentry}),
        conflict_weight=-3,
    ),
    ArticleType.reference: ArticleSignature(
        required_any=frozenset({UnitType.reference, UnitType.fact}),
        supporting=frozenset({UnitType.introduction, UnitType.link_related}),
        neutral=frozenset({UnitType.link_nextstep}),
        excluded=frozenset({UnitType.procedure, UnitType.troubleshooting}),
    ),
    ArticleType.troubleshooting: ArticleSignature(
        required_any=frozenset({UnitType.troubleshooting}),
        supporting=frozenset({UnitType.procedure, UnitType.reference}),
    ),
    ArticleType.glossary: ArticleSignature(
        required_any=frozenset({UnitType.glossary, UnitType.glossentry}),
        supporting=frozenset({UnitType.introduction}),
        excluded=frozenset({UnitType.procedure}),
    ),
    ArticleType.concept: ArticleSignature(
        required_any=frozenset({UnitType.concept, UnitType.principle, UnitType.process}),
        supporting=frozenset({UnitType.introduction, UnitType.link_related}),
        neutral=frozenset({UnitType.prerequisites, UnitType.link_nextstep}),
        excluded=frozenset({UnitType.procedure, UnitType.reference}),
    ),
}

# Minimum margin the winning candidate must beat the runner-up by.
_MIN_MARGIN = 3


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

    # Extract metadata evidence before construction-based triage.
    meta_evidence = _infer_article_type_from_metadata(metadata)

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

    # Determine article type after units exist so construction can inform triage.
    article_type = _select_article_type(meta_evidence, units)
    if article_type == ArticleType.unknown:
        diags.append(DiagnosticFactory.unknown_article_type(source_path=source_path))

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


def _infer_article_type_from_metadata(metadata: dict[str, Any]) -> _MetadataEvidence:
    """Extract article type evidence from front-matter metadata.

    Checks authoritative keys first (direct author declaration), then
    secondary exact keys, then suffix-matched namespaced keys.

    Returns:
        A _MetadataEvidence with candidate_type=unknown and weight=0 when no
        supported key or value is found.
    """
    # Authoritative: direct author declaration — highest weight
    for key in _AUTHORITATIVE_METADATA_KEYS:
        val = metadata.get(key)
        if val:
            mapped = _ARTICLE_TYPE_MAP.get(str(val).lower())
            if mapped is not None:
                return _MetadataEvidence(candidate_type=mapped, weight=10)

    # Secondary exact keys — medium weight
    for key in _SECONDARY_EXACT_KEYS:
        val = metadata.get(key)
        if val:
            mapped = _ARTICLE_TYPE_MAP.get(str(val).lower())
            if mapped is not None:
                return _MetadataEvidence(candidate_type=mapped, weight=6)

    # Suffix-matched namespaced keys (e.g. "ms.topic", "vendor.content_type") — low weight
    for meta_key in metadata:
        if meta_key in _AUTHORITATIVE_METADATA_KEYS or meta_key in _SECONDARY_EXACT_KEYS:
            continue
        for suffix in _METADATA_SUFFIX_PATTERNS:
            if meta_key.endswith(suffix):
                val = metadata.get(meta_key)
                if val:
                    mapped = _ARTICLE_TYPE_MAP.get(str(val).lower())
                    if mapped is not None:
                        return _MetadataEvidence(candidate_type=mapped, weight=4)

    return _MetadataEvidence(candidate_type=ArticleType.unknown, weight=0)


def _select_article_type(
    meta_evidence: _MetadataEvidence,
    units: list[Unit],
) -> ArticleType:
    """Select article type from metadata evidence and unit construction.

    Authoritative metadata (weight ≥ 10) wins immediately. For weaker metadata
    and construction-only signals, uses evidence-based scoring with a minimum
    margin requirement to avoid over-selecting specialised article types.
    """
    # Authoritative metadata wins directly without scoring
    if meta_evidence.candidate_type != ArticleType.unknown and meta_evidence.weight >= 10:
        return meta_evidence.candidate_type

    return _score_article_type(meta_evidence, units)


def _score_article_type(
    meta_evidence: _MetadataEvidence,
    units: list[Unit],
) -> ArticleType:
    """Score article type candidates from metadata and unit evidence.

    Applies per-type minimum score and a global minimum margin. Falls back to
    ``topic`` when known units exist but no specialised type wins by margin,
    or ``unknown`` when there is insufficient evidence to classify at all.
    """
    unit_types = [u.unit_type for u in units]
    known_types = {t for t in unit_types if t != UnitType.unknown}

    scores: dict[ArticleType, _ArticleCandidateScore] = {}

    for article_type, sig in _ARTICLE_SIGNATURES.items():
        # Hard exclusion: any excluded unit disqualifies this type entirely
        if known_types & sig.excluded:
            continue

        # Required unit check: must have at least one required unit
        if sig.required_any and known_types.isdisjoint(sig.required_any):
            continue

        supporting_hit = list(known_types & sig.supporting)
        conflicting_hit = list(known_types & sig.conflicting)

        score = 0
        # Metadata evidence seeds the score for this type
        if meta_evidence.candidate_type == article_type:
            score += meta_evidence.weight

        score += sig.required_weight * len(known_types & sig.required_any)
        score += sig.supporting_weight * len(supporting_hit)
        score += sig.neutral_weight * len(known_types & sig.neutral)
        score += sig.conflict_weight * len(conflicting_hit)

        if score >= sig.min_score:
            scores[article_type] = _ArticleCandidateScore(
                article_type=article_type,
                score=score,
                required_met=True,
                supporting_units=supporting_hit,
                conflicting_units=conflicting_hit,
            )

    # Metadata-only candidate: if metadata points to a type with no matching
    # signature, add it directly so it can still win when units are absent.
    if (
        meta_evidence.candidate_type != ArticleType.unknown
        and meta_evidence.candidate_type not in scores
        and meta_evidence.weight >= 6
    ):
        scores[meta_evidence.candidate_type] = _ArticleCandidateScore(
            article_type=meta_evidence.candidate_type,
            score=meta_evidence.weight,
            required_met=False,
        )

    if not scores:
        # No specialised type qualifies — fall back based on known unit count
        if len(known_types) >= 2:
            return ArticleType.topic
        return ArticleType.unknown

    ordered = sorted(
        scores.values(),
        key=lambda c: (c.score, _article_specificity(c.article_type)),
        reverse=True,
    )
    best = ordered[0]

    if len(ordered) == 1:
        return best.article_type

    # Require a margin over the runner-up to avoid ambiguous over-selection
    if best.score - ordered[1].score >= _MIN_MARGIN:
        return best.article_type

    # Tied or narrow margin — use topic for mixed known content
    if len(known_types) >= 2:
        return ArticleType.topic
    return ArticleType.unknown


def _article_specificity(article_type: ArticleType) -> int:
    """Return a deterministic tie-break priority for construction triage."""
    priority = {
        ArticleType.troubleshooting: 5,
        ArticleType.glossary: 4,
        ArticleType.howto: 3,
        ArticleType.reference: 2,
        ArticleType.concept: 1,
    }
    return priority.get(article_type, 0)


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
        has_ordered_list = any(n.node_type == "list" and n.tag == "ol" for n in nodes)
        has_code_block = any(n.node_type == "code_block" for n in nodes)
        has_paragraphs = any(n.node_type == "paragraph" for n in nodes)

        if heading is None and has_paragraphs and not has_ordered_list:
            # Pre-H2 preamble with introductory paragraphs — classify as introduction
            unit_type = UnitType.introduction
        elif has_ordered_list:
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
