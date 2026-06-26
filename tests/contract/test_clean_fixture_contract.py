"""Contract test: clean fixture produces valid parser output."""
from pathlib import Path

import pytest

from structure_parser import parse_file

CLEAN_FIXTURE = Path(__file__).parent.parent / "fixtures" / "markdown" / "clean.md"


@pytest.fixture
def clean_doc():
    assert CLEAN_FIXTURE.exists(), f"Fixture missing: {CLEAN_FIXTURE}"
    return parse_file(CLEAN_FIXTURE)


class TestCleanFixtureContract:
    def test_has_title(self, clean_doc):
        assert clean_doc.title is not None
        assert len(clean_doc.title) > 0

    def test_has_structured_content(self, clean_doc):
        assert clean_doc.structured_content is not None

    def test_has_units(self, clean_doc):
        assert len(clean_doc.structured_content.content) > 0

    def test_schema_version_present(self, clean_doc):
        assert clean_doc.schema_version == "1"

    def test_source_format_markdown(self, clean_doc):
        from structure_parser.domain.enums import SourceFormat
        assert clean_doc.source_format == SourceFormat.markdown

    def test_no_internal_errors(self, clean_doc):
        internal_errors = [d for d in clean_doc.diagnostics if d.code == "SP-099"]
        assert len(internal_errors) == 0

    def test_metadata_extracted(self, clean_doc):
        assert "title" in clean_doc.metadata or clean_doc.title is not None

    def test_deterministic_output(self):
        doc1 = parse_file(CLEAN_FIXTURE)
        doc2 = parse_file(CLEAN_FIXTURE)
        assert doc1.title == doc2.title
        assert len(doc1.diagnostics) == len(doc2.diagnostics)
        if doc1.structured_content and doc2.structured_content:
            assert len(doc1.structured_content.content) == len(doc2.structured_content.content)
