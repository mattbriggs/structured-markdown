"""Contract test: known-failure fixture produces expected diagnostics."""
from pathlib import Path

import pytest

from structure_parser import parse_file

FAILURE_FIXTURE = Path(__file__).parent.parent / "fixtures" / "markdown" / "known_failure.md"


@pytest.fixture
def failure_doc():
    assert FAILURE_FIXTURE.exists(), f"Fixture missing: {FAILURE_FIXTURE}"
    return parse_file(FAILURE_FIXTURE)


class TestKnownFailureFixtureContract:
    def test_has_diagnostics(self, failure_doc):
        assert len(failure_doc.diagnostics) > 0

    def test_heading_level_skip_detected(self, failure_doc):
        """known_failure.md jumps from H1 to H4."""
        codes = {d.code for d in failure_doc.diagnostics}
        assert "SP-021" in codes  # heading level skipped

    def test_unknown_content_preserved(self, failure_doc):
        """Parser should not crash on unusual structure."""
        # Document should still be parseable
        assert failure_doc.source_path is not None

    def test_no_crash_on_broken_link(self, failure_doc):
        """Broken links should emit diagnostics, not exceptions."""
        # If link resolution is on, unresolved refs should produce SP-050
        # Default mode doesn't resolve, so we just check no crash
        assert failure_doc is not None
