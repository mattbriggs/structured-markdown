"""Tests for transform-readiness evaluators."""
from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.structured_markdown import StructuredContent, Unit
from structure_parser.domain.enums import ArticleType, ReadinessStatus, SourceFormat, UnitType
from structure_parser.readiness.dita import DitaReadinessEvaluator
from structure_parser.readiness.evaluator import evaluate_readiness
from structure_parser.readiness.rag_ingestion import RagIngestionReadinessEvaluator
from structure_parser.readiness.schema_org import SchemaOrgReadinessEvaluator


def _make_doc(title=None, article_type=ArticleType.topic, has_errors=False) -> ParsedDocument:
    sc = StructuredContent(
        article_type=article_type,
        dita_type="topic",
        title=title,
        content=[Unit(unit_type=UnitType.introduction, title="Intro")],
    )
    return ParsedDocument(
        source_path="test.md",
        source_format=SourceFormat.markdown,
        title=title,
        structured_content=sc,
    )


class TestDitaReadiness:
    def test_ready_when_has_title_and_type(self):
        doc = _make_doc(title="My Doc", article_type=ArticleType.howto)
        evaluator = DitaReadinessEvaluator()
        result = evaluator.evaluate(doc)
        assert result.target == "dita"
        assert result.status in (ReadinessStatus.ready, ReadinessStatus.degraded)

    def test_blocked_without_title(self):
        doc = _make_doc(title=None, article_type=ArticleType.unknown)
        evaluator = DitaReadinessEvaluator()
        result = evaluator.evaluate(doc)
        assert result.status in (ReadinessStatus.blocked, ReadinessStatus.degraded)
        assert len(result.prerequisites_missing) > 0


class TestSchemaOrgReadiness:
    def test_degrades_without_description(self):
        doc = _make_doc(title="My Doc")
        evaluator = SchemaOrgReadinessEvaluator()
        result = evaluator.evaluate(doc)
        assert result.target == "schema_org"
        # Either ready or degraded (title present but description missing)
        assert result.status in (ReadinessStatus.ready, ReadinessStatus.degraded)


class TestRagIngestionReadiness:
    def test_ready_with_title_and_content(self):
        doc = _make_doc(title="My Doc")
        evaluator = RagIngestionReadinessEvaluator()
        result = evaluator.evaluate(doc)
        assert result.target == "rag_ingestion"
        assert result.status in (ReadinessStatus.ready, ReadinessStatus.degraded)


class TestEvaluateReadiness:
    def test_runs_all_evaluators(self):
        doc = _make_doc(title="My Doc")
        evaluators = [
            DitaReadinessEvaluator(),
            SchemaOrgReadinessEvaluator(),
            RagIngestionReadinessEvaluator(),
        ]
        result = evaluate_readiness(doc, evaluators)
        assert len(result.targets) == 3
        targets = {t.target for t in result.targets}
        assert "dita" in targets
        assert "schema_org" in targets
        assert "rag_ingestion" in targets
