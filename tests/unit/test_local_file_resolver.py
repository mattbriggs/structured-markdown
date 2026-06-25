"""Tests for the local file reference resolver."""
import tempfile, os
from pathlib import Path
import pytest

from structure_parser.contracts.references import Reference
from structure_parser.resolution.local_file_resolver import LocalFileResolver
from structure_parser.domain.enums import ResolutionState


@pytest.fixture
def resolver():
    return LocalFileResolver()


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


class TestLocalFileResolver:
    def test_resolve_existing_file(self, resolver, tmp_path):
        target = tmp_path / "target.md"
        target.write_text("# Target", encoding="utf-8")
        source = tmp_path / "source.md"
        source.write_text("# Source", encoding="utf-8")

        ref = Reference(ref_type="link", href="./target.md")
        result = resolver.resolve(ref, str(source))
        assert result.state == ResolutionState.resolved

    def test_unresolved_missing_file(self, resolver, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("# Source", encoding="utf-8")

        ref = Reference(ref_type="link", href="./nonexistent.md")
        result = resolver.resolve(ref, str(source))
        assert result.state == ResolutionState.unresolved

    def test_external_url_unsupported(self, resolver, tmp_path):
        source = str(tmp_path / "source.md")
        ref = Reference(ref_type="link", href="https://example.com")
        result = resolver.resolve(ref, source)
        assert result.state == ResolutionState.unsupported

    def test_anchor_only_unsupported(self, resolver, tmp_path):
        source = str(tmp_path / "source.md")
        ref = Reference(ref_type="link", href="#section")
        result = resolver.resolve(ref, source)
        assert result.state == ResolutionState.unsupported

    def test_mailto_unsupported(self, resolver, tmp_path):
        source = str(tmp_path / "source.md")
        ref = Reference(ref_type="link", href="mailto:user@example.com")
        result = resolver.resolve(ref, source)
        assert result.state == ResolutionState.unsupported

    def test_resolved_path_set(self, resolver, tmp_path):
        target = tmp_path / "doc.md"
        target.write_text("# Doc", encoding="utf-8")
        source = str(tmp_path / "source.md")

        ref = Reference(ref_type="link", href="./doc.md")
        result = resolver.resolve(ref, source)
        assert result.resolved_path is not None
        assert "doc.md" in result.resolved_path
