"""Tests for the structured Markdown classifier."""
import tempfile
import os
import pytest
from pathlib import Path

from structure_parser.adapters.markdown import MarkdownAdapter
from structure_parser.contracts.config import ParserConfig
from structure_parser.structured_markdown.classifier import classify
from structure_parser.domain.enums import ArticleType, UnitType, TriageStatus


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
        md = "---\ntitle: T\n---\n# T\n\n## Introduction\n\nX\n\n## Steps\n\n1. A\n\n## Next Steps\n\n- See also\n"
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
