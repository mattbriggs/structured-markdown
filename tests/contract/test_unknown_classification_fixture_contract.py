"""Contract test: unknown-classification fixture preserves unclassified content."""
from pathlib import Path

import pytest

from structure_parser import parse_file
from structure_parser.domain.enums import ArticleType

UNKNOWN_FIXTURE = (
    Path(__file__).parent.parent / "fixtures" / "markdown" / "unknown_classification.md"
)


@pytest.fixture
def unknown_doc():
    assert UNKNOWN_FIXTURE.exists(), f"Fixture missing: {UNKNOWN_FIXTURE}"
    return parse_file(UNKNOWN_FIXTURE)


class TestUnknownClassificationContract:
    def test_document_parsed_successfully(self, unknown_doc):
        assert unknown_doc.source_path is not None
        assert unknown_doc.schema_version == "1"

    def test_article_type_is_unknown(self, unknown_doc):
        if unknown_doc.structured_content:
            assert unknown_doc.structured_content.article_type == ArticleType.unknown

    def test_content_preserved(self, unknown_doc):
        """All content nodes should be preserved even if unclassified."""
        if unknown_doc.structured_content:
            assert len(unknown_doc.structured_content.content) > 0

    def test_unknown_classification_diagnostics_emitted(self, unknown_doc):
        codes = {d.code for d in unknown_doc.diagnostics}
        # SP-041 = unknown article type; SP-040 = unknown unit classification
        assert "SP-041" in codes or "SP-040" in codes
