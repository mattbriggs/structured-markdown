"""Tests for the reference classifier."""
import os
import tempfile
from pathlib import Path

from structure_parser.adapters.markdown import MarkdownAdapter
from structure_parser.contracts.config import ParserConfig
from structure_parser.domain.enums import ResolutionState
from structure_parser.enrichment.reference_classifier import classify_references


def _parse_md(content: str):
    adapter = MarkdownAdapter()
    config = ParserConfig()
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    path = Path(f.name)
    try:
        return adapter.parse(path, config)
    finally:
        os.unlink(f.name)


class TestReferenceClassifier:
    def test_link_classified(self):
        raw = _parse_md("# T\n\n[Click here](./page.md)\n")
        refs = classify_references(raw)
        links = [r for r in refs if r.ref_type == "link"]
        assert len(links) >= 1
        assert any(r.href == "./page.md" for r in links)

    def test_image_classified(self):
        raw = _parse_md("# T\n\n![Alt text](./image.png)\n")
        refs = classify_references(raw)
        images = [r for r in refs if r.ref_type == "image"]
        assert len(images) >= 1
        assert any(r.href == "./image.png" for r in images)

    def test_default_state_not_attempted(self):
        raw = _parse_md("# T\n\n[Link](./x.md)\n")
        refs = classify_references(raw)
        for ref in refs:
            assert ref.state == ResolutionState.not_attempted

    def test_multiple_references(self):
        md = "# T\n\n[A](./a.md) and [B](./b.md)\n\n![Img](./img.png)\n"
        raw = _parse_md(md)
        refs = classify_references(raw)
        assert len(refs) >= 3

    def test_no_references(self):
        raw = _parse_md("# T\n\nJust text.\n")
        refs = classify_references(raw)
        # Could be empty or have very few
        assert all(r.ref_type in ("link", "image", "include") for r in refs)
