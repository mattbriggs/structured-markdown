"""Tests for ParsedDocumentWriter."""
import json
from pathlib import Path

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.pipeline import DiscoveredSource
from structure_parser.domain.enums import SourceFormat
from structure_parser.pipeline.output import ParsedDocumentWriter


def _make_source(tmp_path: Path, relative: str = "index.md") -> DiscoveredSource:
    return DiscoveredSource(
        source_root=tmp_path / "docs",
        source_path=(tmp_path / "docs" / relative).resolve(),
        relative_path=Path(relative),
    )


def _minimal_doc(path: str = "index.md") -> ParsedDocument:
    return ParsedDocument(source_path=path, source_format=SourceFormat.markdown)


class TestTargetPathCalculation:
    def test_appends_json_suffix(self, tmp_path):
        source = _make_source(tmp_path)
        writer = ParsedDocumentWriter()
        target = writer.target_for(source, tmp_path / "out")
        assert target == tmp_path / "out" / "index.md.json"

    def test_preserves_nested_path(self, tmp_path):
        source = _make_source(tmp_path, "guide/install.md")
        writer = ParsedDocumentWriter()
        target = writer.target_for(source, tmp_path / "out")
        assert target == tmp_path / "out" / "guide" / "install.md.json"

    def test_deep_nesting(self, tmp_path):
        source = _make_source(tmp_path, "a/b/c/deep.md")
        writer = ParsedDocumentWriter()
        target = writer.target_for(source, tmp_path / "out")
        assert target == tmp_path / "out" / "a" / "b" / "c" / "deep.md.json"


class TestWriteParsedDocument:
    def test_writes_json_file(self, tmp_path):
        target = tmp_path / "out" / "index.md.json"
        doc = _minimal_doc()
        writer = ParsedDocumentWriter()
        error = writer.write(doc, target)
        assert error is None
        assert target.exists()

    def test_written_content_is_valid_json(self, tmp_path):
        target = tmp_path / "out" / "index.md.json"
        doc = _minimal_doc()
        ParsedDocumentWriter().write(doc, target)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert "source_path" in data

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / "out" / "a" / "b" / "c.md.json"
        ParsedDocumentWriter().write(_minimal_doc(), target)
        assert target.exists()

    def test_dry_run_skips_write(self, tmp_path):
        target = tmp_path / "out" / "index.md.json"
        error = ParsedDocumentWriter().write(_minimal_doc(), target, dry_run=True)
        assert error is None
        assert not target.exists()

    def test_returns_pipe_005_on_write_failure(self, tmp_path):
        # Make the target path a directory so write fails
        bad_target = tmp_path / "out" / "index.md.json"
        bad_target.mkdir(parents=True)
        error = ParsedDocumentWriter().write(_minimal_doc(), bad_target)
        assert error == "PIPE-005"


class TestOverlapDetection:
    def test_no_overlap_clean(self, tmp_path):
        (tmp_path / "docs").mkdir()
        result = ParsedDocumentWriter.check_overlap(
            [tmp_path / "docs"], tmp_path / "out"
        )
        assert result is False

    def test_output_inside_input_is_overlap(self, tmp_path):
        (tmp_path / "docs").mkdir()
        result = ParsedDocumentWriter.check_overlap(
            [tmp_path / "docs"], tmp_path / "docs" / "out"
        )
        assert result is True

    def test_missing_input_skipped(self, tmp_path):
        result = ParsedDocumentWriter.check_overlap(
            [tmp_path / "missing"], tmp_path / "out"
        )
        assert result is False


class TestDuplicateTargetDetection:
    def test_no_duplicates_clean(self, tmp_path):
        sources = [
            _make_source(tmp_path, "a.md"),
            _make_source(tmp_path, "b.md"),
        ]
        duplicates = ParsedDocumentWriter.check_duplicate_targets(sources, tmp_path / "out")
        assert duplicates == []

    def test_detects_duplicate_relative_paths(self, tmp_path):
        # Two sources that share the same relative path produce duplicate targets
        src1 = DiscoveredSource(
            source_root=tmp_path / "root1",
            source_path=tmp_path / "root1" / "index.md",
            relative_path=Path("index.md"),
        )
        src2 = DiscoveredSource(
            source_root=tmp_path / "root2",
            source_path=tmp_path / "root2" / "index.md",
            relative_path=Path("index.md"),
        )
        duplicates = ParsedDocumentWriter.check_duplicate_targets(
            [src1, src2], tmp_path / "out"
        )
        assert "index.md" in duplicates
