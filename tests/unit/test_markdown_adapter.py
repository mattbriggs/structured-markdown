"""Tests for the Markdown adapter."""
import tempfile
import os
import pytest
from pathlib import Path

from structure_parser.adapters.markdown import MarkdownAdapter
from structure_parser.contracts.config import ParserConfig
from structure_parser.domain.enums import SourceFormat


CLEAN_MD = """\
---
title: Test Document
articleType: howto
---

# Test Document

## Introduction

This is a paragraph with **bold** and *italic* text.

## Steps

1. Step one
2. Step two

## Code Example

```python
print("hello")
```

## Next Steps

- [See docs](./docs.md)
"""

FRONT_MATTER_ONLY = """\
---
title: Minimal
---

# Minimal

A paragraph.
"""

NO_FRONT_MATTER = """\
# No Front Matter

Just a paragraph.
"""


@pytest.fixture
def adapter():
    return MarkdownAdapter()


@pytest.fixture
def config():
    return ParserConfig()


def _write_temp(content: str, suffix: str = ".md") -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestMarkdownAdapter:
    def test_source_format(self, adapter):
        assert adapter.source_format == "markdown"

    def test_supported_extensions(self, adapter):
        assert ".md" in adapter.supported_extensions
        assert ".markdown" in adapter.supported_extensions

    def test_parse_clean_document(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            assert raw.source_format == SourceFormat.markdown
            assert raw.source_path == str(path)
            assert raw.content_hash is not None
            assert raw.front_matter.get("title") == "Test Document"
            assert raw.front_matter.get("articleType") == "howto"
            assert len(raw.nodes) > 0
        finally:
            os.unlink(path)

    def test_parse_headings(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            headings = [n for n in raw.nodes if n.node_type == "heading"]
            assert any(n.level == 1 for n in headings)
            assert any(n.level == 2 for n in headings)
            h1 = next(n for n in headings if n.level == 1)
            assert h1.content == "Test Document"
        finally:
            os.unlink(path)

    def test_parse_paragraphs(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            paragraphs = [n for n in raw.nodes if n.node_type == "paragraph"]
            assert len(paragraphs) >= 1
        finally:
            os.unlink(path)

    def test_parse_ordered_list(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            lists = [n for n in raw.nodes if n.node_type == "list"]
            ordered = [l for l in lists if l.tag == "ol"]
            assert len(ordered) >= 1
            assert len(ordered[0].children) == 2
        finally:
            os.unlink(path)

    def test_parse_code_block(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            code_blocks = [n for n in raw.nodes if n.node_type == "code_block"]
            assert len(code_blocks) >= 1
            assert code_blocks[0].attrs.get("language") == "python"
        finally:
            os.unlink(path)

    def test_parse_no_front_matter(self, adapter, config):
        path = _write_temp(NO_FRONT_MATTER)
        try:
            raw = adapter.parse(path, config)
            assert raw.front_matter == {}
            assert raw.front_matter_error is None
        finally:
            os.unlink(path)

    def test_parse_content_hash(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw1 = adapter.parse(path, config)
            raw2 = adapter.parse(path, config)
            assert raw1.content_hash == raw2.content_hash
        finally:
            os.unlink(path)

    def test_parse_line_numbers(self, adapter, config):
        path = _write_temp(CLEAN_MD)
        try:
            raw = adapter.parse(path, config)
            headings = [n for n in raw.nodes if n.node_type == "heading"]
            for h in headings:
                if h.start_line is not None:
                    assert h.start_line >= 1
        finally:
            os.unlink(path)
