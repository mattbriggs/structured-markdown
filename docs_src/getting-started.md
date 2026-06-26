# Getting Started

`structure_parser` turns a plain Markdown file into a classified, schema-validated, diagnostic-annotated content model in a single command or a single Python call. This guide walks from installation through your first parse, the inspection commands, schema validation, the Python API, and running the test suite.

## Installation

`structure_parser` requires Python 3.12 or later. Install it from PyPI into your active virtual environment:

```bash
pip install structure-parser
```

For development — contributing to the package, running tests, or building documentation — install the editable package with the `[dev]` extras:

```bash
git clone https://github.com/mb/structured-markdown
cd structured-markdown
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

The `[dev]` extras include pytest, pytest-cov, ruff, mypy, and mkdocs-material. The editable install (`-e`) means changes to the `src/structure_parser/` source tree take effect immediately without reinstalling.

## Your First Parse

Create a minimal Markdown file named `install-widget.md` with the following content:

```markdown
---
title: How to Install the Widget
articleType: howto
author: Jane Smith
---

# How to Install the Widget

## Introduction

The Widget is a command-line tool that manages widget configurations. Install it before running any widget commands.

## Prerequisites

- Python 3.12 or later installed
- A valid widget license key
- Write access to `/etc/widget/`

## Steps

1. Download the widget installer from the releases page.
2. Run `widget-install --license YOUR_KEY`.
3. Verify the installation with `widget --version`.

## Next Steps

- [Configure the Widget](./configure-widget.md)
- [Widget Command Reference](./widget-reference.md)
```

Parse it with the CLI:

```bash
structure-parser parse install-widget.md
```

The output summarizes the parse result:

```
install-widget.md
  title:        How to Install the Widget
  article_type: howto
  info_type:    mixed
  units:        4
  diagnostics:  0 errors, 0 warnings
  readiness:    DITA=ready  Schema.org=ready  RAG=ready
```

Each field tells you something specific. `article_type: howto` confirms that the parser read the `articleType: howto` front matter field and mapped it to the `howto` article type. `units: 4` means the parser found four H2 sections — Introduction, Prerequisites, Steps, and Next Steps — and classified each as a typed unit. `diagnostics: 0 errors, 0 warnings` means the content conforms to the Structured Markdown pattern language. `readiness` summarizes the transform-readiness evaluation for three downstream targets: DITA XML output, Schema.org structured data, and RAG ingestion chunk boundaries.

## Inspecting the Model

Four `inspect-*` commands let you examine different aspects of a parsed document.

`inspect-model` shows the full Article → Unit → Component classification:

```bash
structure-parser inspect-model install-widget.md
```

```
Article: howto  (information_type: mixed)
  Unit: introduction  "Introduction"
    compParagraph
  Unit: prerequisites  "Prerequisites"
    compListUnordered  (3 items)
  Unit: procedure  "Steps"
    compListOrdered  (3 items)
  Unit: link-nextstep  "Next Steps"
    compListUnordered  (2 items)
```

`inspect-structure` shows the heading tree with nesting depth and triage status:

```bash
structure-parser inspect-structure install-widget.md
```

`inspect-references` lists every link and image found in the document, along with its resolution state:

```bash
structure-parser inspect-references install-widget.md
```

```
References (2)
  [link]  ./configure-widget.md   not_attempted
  [link]  ./widget-reference.md   not_attempted
```

By default, reference resolution is disabled (`resolve_local_references=False`). References appear with state `not_attempted`. Pass `--resolve` or set `resolve_local_references=True` in a `ParserConfig` to attempt local file resolution, which changes the state to `resolved` or `unresolved` (SP-050).

`inspect-diagnostics` shows all diagnostics grouped by severity:

```bash
structure-parser inspect-diagnostics install-widget.md
```

When a document parses cleanly, this command reports no diagnostics. For a document missing its H1 title, the output would include:

```
Warnings (1)
  SP-020  [warning]  Document is missing an H1 title.
```

## Validating Against a Schema

`validate-markdown` parses the document and validates its `StructuredContent` output against a specific JSON schema from the `model/` directory:

```bash
structure-parser validate-markdown install-widget.md --schema artHowto.schema.json
```

The `artHowto.schema.json` schema enforces the structural expectations for a howto article: the presence of a procedure unit, the expected unit ordering, and required article-level metadata. When validation passes:

```
install-widget.md  PASS  (advisory)
```

When validation finds a gap, the output names the failing constraint and the SP-030 diagnostic that records it. By default, validation runs in advisory mode: schema violations produce warnings, not errors, and the exit code remains 0. Add `--strict` to treat all validation warnings as errors and exit with code 1:

```bash
structure-parser validate-markdown install-widget.md --schema artHowto.schema.json --strict
```

The `artArticle.schema.json` schema is a union type that accepts any article type. Use it as a permissive default when you want validation without type-specific constraints.

## Python API Quick Start

The `parse_file` function is the primary Python entry point. It returns a `ParsedDocument` Pydantic model that exposes the full parse result:

```python
from structure_parser import parse_file

doc = parse_file("install-widget.md")

# Article-level fields
print(doc.title)                                    # "How to Install the Widget"
print(doc.structured_content.article_type)          # ArticleType.howto
print(doc.structured_content.information_type)      # InformationType.mixed

# Iterate over units
for unit in doc.structured_content.content:
    comp_count = len(unit.content)
    print(f"  {unit.unit_type.value}: {unit.title}  ({comp_count} components)")

# Check diagnostics
if doc.has_errors:
    for d in doc.diagnostics:
        if d.severity.value == "error":
            print(f"[{d.code}] {d.message}")

# Check transform readiness
for target in doc.readiness.targets:
    print(f"{target.target}: {target.status.value}")
```

`parse_files` parses multiple files in a single call and returns a `ParseRunResult` with aggregate statistics:

```python
from structure_parser import parse_files

result = parse_files(["article1.md", "article2.md", "article3.md"])
print(f"Parsed {result.stats.file_count} files")
print(f"Errors: {result.stats.error_count}  Warnings: {result.stats.warning_count}")
print(f"Duration: {result.stats.duration_ms:.0f}ms")

for doc in result.documents:
    status = "ERROR" if doc.has_errors else "OK"
    print(f"  [{status}] {doc.source_path}")
```

## ParserConfig

`ParserConfig` is an immutable Pydantic model that controls parser behavior. Pass it to `parse_file` or `parse_files` to override defaults:

```python
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig

config = ParserConfig(
    validation_mode="strict",          # "advisory" (default) or "strict"
    resolve_local_references=True,     # attempt to resolve ./link.md paths
    emit_debug_logs=True,              # structured debug logs to stderr
)
doc = parse_file("install-widget.md", config=config)
```

The key fields:

- `validation_mode` — `"advisory"` (default): schema violations are warnings, exit code 0. `"strict"`: schema violations are errors, exit code 1.
- `resolve_local_references` — `False` (default): references are classified but not resolved. `True`: the parser attempts to open local file paths relative to the source file and emits SP-050 for any that do not exist.
- `emit_debug_logs` — `False` (default): no debug output. `True`: structured JSON logs go to stderr, covering adapter token streams, classification decisions, and validation steps.
- `model_schema_dir` — `None` (default): uses the schemas bundled in the installed package under `model/`. Set to a `Path` to use a custom schema directory.
- `max_diagnostic_count` — `500` (default): caps the number of diagnostics in a single document result to prevent unbounded output on pathological inputs.

`ParserConfig` is frozen — fields cannot be changed after construction. Create a new instance to use different settings.

## Running Tests

Run the full test suite with:

```bash
pytest
```

Run with coverage reporting:

```bash
pytest --cov=structure_parser --cov-report=term-missing
```

The test suite is organized in three layers:

```bash
pytest tests/unit/         # unit tests for individual models and services
pytest tests/contract/     # fixture-based contract tests
pytest tests/integration/  # end-to-end CLI and API tests
```

Validate the fixture files against expected contract outputs:

```bash
python tools/validate_fixtures.py
```

Update expected contract fixtures after intentional parser behavior changes:

```bash
python tools/update_expected_contracts.py
```
