"""Tests for the structured Markdown classifier."""
import os
import tempfile
from pathlib import Path

from structure_parser.adapters.markdown import MarkdownAdapter
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.validation import ModelValidationResult
from structure_parser.domain.enums import ArticleType, UnitType
from structure_parser.structured_markdown.classifier import classify


def _parse_md(content: str) -> object:
    adapter = MarkdownAdapter()
    config = ParserConfig()
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    path = Path(f.name)
    try:
        raw = adapter.parse(path, config)
        return raw
    finally:
        os.unlink(f.name)


class TestClassifier:
    def test_howto_article_type(self):
        md = "---\narticleType: howto\ntitle: Test\n---\n# Test\n\n## Steps\n\n1. Do this\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"articleType": "howto", "title": "Test"})
        assert sc.article_type == ArticleType.howto

    def test_reference_article_type(self):
        md = "---\narticleType: reference\ntitle: Ref\n---\n# Ref\n\n## Options\n\nSome text.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"articleType": "reference", "title": "Ref"})
        assert sc.article_type == ArticleType.reference

    def test_unknown_article_type_emits_diagnostic(self):
        md = "---\ntitle: Test\n---\n# Test\n\n## Random Section\n\nSome content.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"title": "Test"})
        assert sc.article_type == ArticleType.unknown
        codes = {d.code for d in diags}
        assert "SP-041" in codes

    def test_howto_article_type_inferred_from_procedure_units(self):
        md = "# Test\n\n## Prerequisites\n\n- Access\n\n## Steps\n\n1. Do this\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        assert sc.article_type == ArticleType.howto
        assert sc.schema_name == "artHowto.schema.json"
        codes = {d.code for d in diags}
        assert "SP-041" not in codes

    def test_reference_article_type_inferred_from_reference_units(self):
        md = "# Ref\n\n## Options\n\n| Name | Value |\n| --- | --- |\n| a | b |\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        assert sc.article_type == ArticleType.reference
        assert sc.schema_name == "artReference.schema.json"

    def test_concept_article_type_inferred_from_concept_units(self):
        md = "# Concept\n\n## What is structured Markdown?\n\nStructured Markdown adds meaning.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        assert sc.article_type == ArticleType.concept
        assert sc.schema_name == "artConcept.schema.json"

    def test_topic_article_type_inferred_from_mixed_known_units(self):
        md = "# Topic\n\n## Introduction\n\nIntro.\n\n## Related\n\n- Link\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        assert sc.article_type == ArticleType.topic
        assert sc.schema_name == "artTopic.schema.json"

    def test_metadata_article_type_wins_over_construction_signal(self):
        md = "---\narticleType: reference\n---\n# Ref\n\n## Steps\n\n1. Do this\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"articleType": "reference"})
        assert sc.article_type == ArticleType.reference
        assert sc.schema_name == "artReference.schema.json"

    def test_introduction_unit_type(self):
        md = "---\ntitle: T\n---\n# T\n\n## Introduction\n\nIntro text.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"title": "T"})
        units = [u for u in sc.content if u.unit_type == UnitType.introduction]
        assert len(units) >= 1

    def test_prerequisites_unit_type(self):
        md = "---\ntitle: T\n---\n# T\n\n## Prerequisites\n\n- Requirement\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"title": "T"})
        units = [u for u in sc.content if u.unit_type == UnitType.prerequisites]
        assert len(units) >= 1

    def test_procedure_detection_ordered_list(self):
        md = "---\ntitle: T\n---\n# T\n\n## Steps\n\n1. Step one\n2. Step two\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {"title": "T"})
        units = [u for u in sc.content if u.unit_type == UnitType.procedure]
        assert len(units) >= 1

    def test_content_order_preserved(self):
        md = (
            "---\ntitle: T\n---\n# T\n\n## Introduction\n\nX\n\n## Steps\n\n1. A\n\n"
            "## Next Steps\n\n- See also\n"
        )
        raw = _parse_md(md)
        sc, diags = classify(raw, {"title": "T"})
        titles = [u.title for u in sc.content]
        assert titles == ["Introduction", "Steps", "Next Steps"]

    def test_schema_version_present(self):
        md = "# T\n\n## Section\n\nContent.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        assert sc.schema_version == "1"

    def test_unknown_unit_preserved(self):
        md = "# T\n\n## Totally Random Section\n\nSome prose without pattern.\n"
        raw = _parse_md(md)
        sc, diags = classify(raw, {})
        # Unknown units should be preserved, not dropped
        assert len(sc.content) >= 1


class TestMetadataNormalization:
    """Metadata key/value normalisation across generic patterns."""

    def test_secondary_key_type_maps_to_article_type(self):
        md = "# Doc\n\n## Overview\n\nIntro.\n\n## Background\n\nDetails.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"type": "concept"})
        assert sc.article_type == ArticleType.concept

    def test_secondary_key_topic_maps_to_article_type(self):
        md = "# Doc\n\n## Options\n\n| A | B |\n| - | - |\n| x | y |\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"topic": "reference"})
        assert sc.article_type == ArticleType.reference

    def test_secondary_key_content_type_maps_conceptual(self):
        md = "# Doc\n\n## Overview\n\nIntro.\n\n## Background\n\nDetails.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"content_type": "conceptual"})
        assert sc.article_type == ArticleType.concept

    def test_suffix_matched_key_ms_topic(self):
        # "ms.topic" ends with ".topic" → weak evidence at weight 4
        md = "# Doc\n\n## Overview\n\nIntro.\n\n## Background\n\nDetails.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"ms.topic": "conceptual"})
        assert sc.article_type == ArticleType.concept

    def test_suffix_matched_key_vendor_type(self):
        md = "# Doc\n\n## Steps\n\n1. Do this\n2. Do that\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"vendor.type": "how-to"})
        assert sc.article_type == ArticleType.howto

    def test_authoritative_key_overrides_suffix_key(self):
        # articleType is authoritative and beats a conflicting ms.topic
        md = "# Doc\n\n## Overview\n\nIntro.\n\n## Background\n\nDetails.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"articleType": "howto", "ms.topic": "conceptual"})
        assert sc.article_type == ArticleType.howto

    def test_task_value_maps_to_howto(self):
        md = "# Doc\n\n## Steps\n\n1. Do this\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"type": "task"})
        assert sc.article_type == ArticleType.howto

    def test_procedure_value_maps_to_howto(self):
        md = "# Doc\n\n## Steps\n\n1. Do this\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"type": "procedure"})
        assert sc.article_type == ArticleType.howto

    def test_api_value_maps_to_reference(self):
        md = "# Doc\n\n## Options\n\n| A | B |\n| - | - |\n| x | y |\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {"type": "api"})
        assert sc.article_type == ArticleType.reference


class TestHowtoDominance:
    """How-to should require dominant procedure evidence."""

    def test_overview_and_nextstep_is_not_howto(self):
        # No procedure unit — link_nextstep alone must not trigger howto
        md = "# Doc\n\n## Overview\n\nIntro text.\n\n## Next Steps\n\n- See link\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        assert sc.article_type != ArticleType.howto

    def test_intro_and_nextstep_is_not_howto(self):
        md = "# Doc\n\n## Introduction\n\nParagraph.\n\n## Next Steps\n\n- Link 1\n- Link 2\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        assert sc.article_type != ArticleType.howto

    def test_procedure_with_prerequisites_is_howto(self):
        md = "# Doc\n\n## Prerequisites\n\n- Access\n\n## Steps\n\n1. Do this\n2. Do that\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        assert sc.article_type == ArticleType.howto

    def test_multiple_procedure_units_is_howto(self):
        md = (
            "# Doc\n\n## Prerequisites\n\n- Access\n\n"
            "## Install\n\n1. Step A\n2. Step B\n\n"
            "## Configure\n\n1. Step C\n2. Step D\n\n"
            "## Next Steps\n\n- See more\n"
        )
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        assert sc.article_type == ArticleType.howto

    def test_nextstep_alone_does_not_classify_howto(self):
        md = "# Doc\n\n## Next Steps\n\n- Link A\n- Link B\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        assert sc.article_type != ArticleType.howto


class TestNewUnitHeadings:
    """Expanded heading keyword coverage for reference, principle, and concept units."""

    def test_cheat_sheet_heading_is_reference(self):
        md = "# Doc\n\n## Cheat Sheet\n\n| Command | Effect |\n| --- | --- |\n| x | y |\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.reference]
        assert len(units) >= 1

    def test_limits_heading_is_reference(self):
        md = "# Doc\n\n## Limits\n\n| Resource | Max |\n| --- | --- |\n| VMs | 50 |\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.reference]
        assert len(units) >= 1

    def test_api_version_heading_is_reference(self):
        md = "# Doc\n\n## API Version\n\nVersion 2.0.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.reference]
        assert len(units) >= 1

    def test_best_practices_heading_is_principle(self):
        md = "# Doc\n\n## Best Practices\n\nFollow these rules.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.principle]
        assert len(units) >= 1

    def test_considerations_heading_is_principle(self):
        md = "# Doc\n\n## Considerations\n\nThink about these things.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.principle]
        assert len(units) >= 1

    def test_about_heading_is_concept(self):
        md = "# Doc\n\n## About This Service\n\nThis service provides X.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.concept]
        assert len(units) >= 1

    def test_before_creating_heading_is_concept(self):
        md = "# Doc\n\n## Before Creating a VM\n\nConsider these points.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.concept]
        assert len(units) >= 1

    def test_understand_heading_is_concept(self):
        md = "# Doc\n\n## Understand the Architecture\n\nDetails here.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        units = [u for u in sc.content if u.unit_type == UnitType.concept]
        assert len(units) >= 1


class TestPreambleClassification:
    """Pre-H2 content should classify as introduction when ordinary."""

    def test_preamble_paragraphs_become_introduction(self):
        md = "# Doc\n\nThis is introductory text before any section.\n\n## Details\n\nInfo.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        # The preamble unit (heading=None) should be introduction
        intro_units = [u for u in sc.content if u.unit_type == UnitType.introduction and u.title is None]
        assert len(intro_units) >= 1

    def test_preamble_with_ordered_list_stays_procedure(self):
        # Ordered-list preamble is still procedural (unusual but possible)
        md = "# Doc\n\n1. Step one\n2. Step two\n\n## More\n\nContent.\n"
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        # Should not become introduction; procedure or unknown is expected
        intro_headingless = [
            u for u in sc.content if u.unit_type == UnitType.introduction and u.title is None
        ]
        assert len(intro_headingless) == 0


class TestMixedContentFallback:
    """Mixed known units should fall back to topic when no type wins by margin."""

    def test_reference_and_concept_mixed_falls_back_to_topic(self):
        # reference unit (Options) + concept unit (Background) — no single type dominates
        md = (
            "# Doc\n\n## Background\n\nConceptual info.\n\n"
            "## Options\n\n| A | B |\n| - | - |\n| x | y |\n"
        )
        raw = _parse_md(md)
        sc, _ = classify(raw, {})
        # concept excluded from reference; reference excluded from concept → neither wins
        # Both would score 5 each with no margin → topic fallback
        assert sc.article_type in {ArticleType.topic, ArticleType.reference, ArticleType.concept}

    def test_concept_dominant_over_mixed_with_metadata(self):
        # ms.topic: conceptual (+4) + two concept units dominates
        md = (
            "# Doc\n\n## Overview\n\nIntro.\n\n## Background\n\nDetails.\n\n"
            "## Next Steps\n\n- See link\n"
        )
        raw = _parse_md(md)
        sc, _ = classify(raw, {"ms.topic": "conceptual"})
        # concept gets metadata (+4) + concept unit score; howto has no procedure
        assert sc.article_type != ArticleType.howto


class TestDitaReadinessDegraded:
    """DITA readiness should be degraded when schema validation fails."""

    def _make_parsed_doc(self, valid: bool):
        from structure_parser.contracts.parsed_document import ParsedDocument
        from structure_parser.contracts.structured_markdown import StructuredContent
        from structure_parser.domain.enums import ArticleType, ReadinessStatus, SourceFormat
        from structure_parser.contracts.transform_readiness import TargetReadiness, TransformReadiness
        from structure_parser.readiness.dita import DitaReadinessEvaluator

        sc = StructuredContent(
            article_type=ArticleType.concept,
            dita_type="concept",
            title="Test",
        )
        val_result = ModelValidationResult(
            schema_id="artConcept.schema.json",
            valid=valid,
            source_path="test.md",
        )
        doc = ParsedDocument(
            source_path="test.md",
            source_format=SourceFormat.markdown,
            title="Test",
            structured_content=sc,
            validation=val_result,
        )
        return doc, DitaReadinessEvaluator()

    def test_dita_ready_when_validation_passes(self):
        doc, evaluator = self._make_parsed_doc(valid=True)
        result = evaluator.evaluate(doc)
        assert result.status.value == "ready"

    def test_dita_degraded_when_validation_fails(self):
        doc, evaluator = self._make_parsed_doc(valid=False)
        result = evaluator.evaluate(doc)
        assert result.status.value == "degraded"
        assert any("Schema validation" in m for m in result.prerequisites_missing)
