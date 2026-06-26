"""End-to-end parse integration tests."""
import os
import tempfile
from pathlib import Path

from structure_parser import parse_file, parse_files
from structure_parser.domain.enums import ArticleType, SourceFormat

HOWTO_MD = """\
---
title: How to Do Something
articleType: howto
---

# How to Do Something

## Introduction

This guide shows you how to do something.

## Prerequisites

- Python 3.11+

## Steps

1. Open a terminal
2. Run the command

## Next Steps

- [See more](./more.md)
"""

CONCEPT_MD = """\
---
title: Understanding the Model
articleType: concept
---

# Understanding the Model

## Introduction

The model is a layered system.

## Key Concepts

Concepts are mapped to units.
"""


def _tmp_file(content: str, suffix: str = ".md") -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestParseFileEndToEnd:
    def test_parse_howto_article_type(self):
        path = _tmp_file(HOWTO_MD)
        try:
            doc = parse_file(path)
            assert doc.title == "How to Do Something"
            assert doc.source_format == SourceFormat.markdown
            if doc.structured_content:
                assert doc.structured_content.article_type == ArticleType.howto
        finally:
            os.unlink(path)

    def test_parse_returns_valid_schema_version(self):
        path = _tmp_file(HOWTO_MD)
        try:
            doc = parse_file(path)
            assert doc.schema_version == "1"
        finally:
            os.unlink(path)

    def test_parse_includes_readiness(self):
        path = _tmp_file(HOWTO_MD)
        try:
            doc = parse_file(path)
            assert doc.readiness is not None
            assert len(doc.readiness.targets) > 0
        finally:
            os.unlink(path)

    def test_parse_includes_structure(self):
        path = _tmp_file(HOWTO_MD)
        try:
            doc = parse_file(path)
            assert doc.structure is not None
            assert doc.structure.has_title
        finally:
            os.unlink(path)

    def test_parse_missing_file_returns_diagnostic(self):
        doc = parse_file("/tmp/absolutely-does-not-exist-xyz.md")
        assert doc.has_errors
        assert any(
            d.code in ("SP-001", "SP-003", "SP-099") for d in doc.diagnostics
        )


class TestParseFilesEndToEnd:
    def test_parse_multiple_files(self):
        p1 = _tmp_file(HOWTO_MD)
        p2 = _tmp_file(CONCEPT_MD)
        try:
            result = parse_files([p1, p2])
            assert result.stats.file_count == 2
            assert len(result.documents) == 2
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_stats_populated(self):
        path = _tmp_file(HOWTO_MD)
        try:
            result = parse_files([path])
            assert result.stats.duration_ms is not None
            assert result.stats.duration_ms >= 0
        finally:
            os.unlink(path)
