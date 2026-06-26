# Structured Markdown Parser

A layered Python package that parses Markdown and rendered HTML into a normalized structured content hierarchy for validation, publishing transforms, and RAG ingestion.

The parser maps source files into an **Article → Unit → Component → Attribute** hierarchy defined by the JSON schemas in [`model/`](model/). It produces versioned Pydantic contracts, author-facing diagnostics, and transform-readiness reports — with a CLI and a Python API.

## MVP Scope

| Capability | Status |
|---|---|
| Markdown parsing (`.md`) | Complete |
| Rendered HTML parsing (`.html`) | Complete |
| YAML front matter extraction | Complete |
| Article/unit/component/attribute classification | Complete |
| JSON Schema validation against `model/` | Complete (advisory) |
| Reference classification | Complete |
| Local file reference resolution | Complete |
| Author-facing diagnostics (stable codes) | Complete |
| Transform-readiness evaluation (DITA, Schema.org, RAG) | Complete |
| CLI commands | Complete |
| Python API | Complete |
| DITA/XML parsing | Deferred (A-004) |
| Complex conref/keyref resolution | Deferred (A-005) |

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

## Basic CLI Usage

Parse a file and inspect the structured content model:

```bash
structure-parser parse my-article.md
structure-parser inspect-model my-article.md
structure-parser inspect-structure my-article.md
structure-parser inspect-references my-article.md
structure-parser inspect-diagnostics my-article.md
structure-parser transform-readiness my-article.md
```

Validate against a specific schema:

```bash
structure-parser validate-markdown my-article.md --schema artHowto.schema.json
structure-parser validate-markdown my-article.md --schema artArticle.schema.json --strict
```

Output as JSON:

```bash
structure-parser parse my-article.md --json
```

## Basic Python API Usage

```python
from structure_parser import parse_file, parse_files
from structure_parser.contracts.config import ParserConfig

# Parse a single file (uses default config)
doc = parse_file("my-article.md")

print(doc.title)                                  # "How to Configure Settings"
print(doc.structured_content.article_type)        # ArticleType.howto
print(doc.structured_content.information_type)    # InformationType.mixed

for unit in doc.structured_content.content:
    print(f"  {unit.unit_type.value}: {unit.title}")

# Check diagnostics
if doc.has_errors:
    for d in doc.diagnostics:
        print(f"[{d.severity.value}] {d.code}: {d.message}")

# Check transform readiness
for target in doc.readiness.targets:
    print(f"{target.target}: {target.status.value}")

# Parse multiple files
result = parse_files(["article1.md", "article2.md"])
print(f"Parsed {result.stats.file_count} files in {result.stats.duration_ms:.0f}ms")
```

Configuration:

```python
config = ParserConfig(
    validation_mode="strict",           # "advisory" (default) or "strict"
    resolve_local_references=True,      # resolve ./link.md paths
    enable_structured_markdown=True,    # article/unit/component classification
    emit_debug_logs=True,               # structured logs to stderr
)
doc = parse_file("my-article.md", config=config)
```

## Example Normalized JSON Output

```json
{
  "schema_version": "1",
  "source_path": "tests/fixtures/markdown/clean.md",
  "title": "How to Configure Settings",
  "article_type": "howto",
  "information_type": "mixed",
  "units": [
    {"unit_type": "introduction", "title": "Introduction", "component_count": 1},
    {"unit_type": "prerequisites", "title": "Prerequisites", "component_count": 2},
    {"unit_type": "procedure", "title": "Steps", "component_count": 1},
    {"unit_type": "procedure", "title": "Example Configuration", "component_count": 1},
    {"unit_type": "link-nextstep", "title": "Next Steps", "component_count": 2}
  ],
  "references": [
    {"type": "link", "href": "./deploy.md"},
    {"type": "link", "href": "./monitor.md"}
  ],
  "diagnostic_count": 1
}
```

Full JSON output (with `--json` flag or `model_dump()`):

```bash
structure-parser parse tests/fixtures/markdown/clean.md --json
```

## Diagnostic Codes

| Code | Severity | Meaning |
|---|---|---|
| `SP-001` | error | Source file not found |
| `SP-002` | error | Unsupported source format |
| `SP-003` | error | Parse failed |
| `SP-010` | warning | Malformed YAML front matter |
| `SP-011` | info | Front matter absent |
| `SP-020` | warning | Missing H1 title |
| `SP-021` | warning | Heading level skipped |
| `SP-030` | warning | Schema validation failed |
| `SP-031` | error | Schema file not found |
| `SP-040` | info | Content classified as unknown |
| `SP-041` | warning | Article type could not be determined |
| `SP-050` | warning | Unresolved local reference |
| `SP-060` | info | Transform readiness status |
| `SP-099` | error | Internal parser error |

## Architecture

```
Markdown / HTML
      │
      ▼
Format Adapter (adapters/)
      │ RawParseModel
      ▼
Semantic Enricher (enrichment/)
   ├── Metadata Extractor
   ├── Structure Builder
   ├── Reference Classifier
   └── Structured Markdown Classifier (structured_markdown/)
         │ StructuredContent
         ▼
   Model Validator (validation/)
         │
         ▼
   Readiness Evaluator (readiness/)
         │
         ▼
ParsedDocument (contracts/parsed_document.py)
      │
      ├── CLI (cli.py)         → human text / JSON
      ├── API (api.py)         → Pydantic models
      └── Debug Inspector      → structured reports
```

### Layer Contracts

| Layer | Input | Output |
|---|---|---|
| `adapters/` | Source file | `RawParseModel` |
| `enrichment/` | `RawParseModel` | `ParsedDocument` partials |
| `structured_markdown/` | `RawParseModel` | `StructuredContent` |
| `validation/` | `StructuredContent` | `ModelValidationResult` |
| `readiness/` | `ParsedDocument` | `TransformReadiness` |
| `api.py` | File path + config | `ParsedDocument` / `ParseRunResult` |

## Model Directory

The `model/` directory contains the authoritative JSON schemas for the structured Markdown pattern language:

```
model/
├── articles/
│   ├── artArticle.schema.json        # Union of all article types
│   ├── artHowto.schema.json
│   ├── artConcept.schema.json
│   ├── artReference.schema.json
│   └── units/
│       ├── sharedUnits.schema.json
│       ├── unitIntroduction.schema.json
│       ├── unitProcedure.schema.json
│       └── components/
│           ├── compParagraph.schema.json
│           ├── compBlockCode.schema.json
│           ├── compTable.schema.json
│           └── attributes/
│               ├── attText.schema.json
│               ├── attLink.schema.json
│               └── attImage.schema.json
├── model-overview.md
└── schema-index.md
```

See [model/model-overview.md](model/model-overview.md) and [model/schema-index.md](model/schema-index.md) for the full schema hierarchy.

## Development Setup

```bash
git clone https://github.com/mb/structured-markdown
cd structured-markdown

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Test and Coverage Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=structure_parser --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only contract tests
pytest tests/contract/

# Run only integration tests
pytest tests/integration/

# Validate fixtures
python tools/validate_fixtures.py
```

## Documentation Build Commands

```bash
# MkDocs Material live preview
mkdocs serve

# MkDocs static build
mkdocs build

# Generate JSON Schema artifacts from Pydantic models
python tools/generate_json_schemas.py

# Update expected contract fixtures from current parser output
python tools/update_expected_contracts.py
```

## CLI Reference

| Command | Description |
|---|---|
| `structure-parser parse PATH...` | Parse one or more files; output summary or JSON |
| `structure-parser validate-markdown PATH... [--schema ID] [--strict]` | Validate structured Markdown authoring model |
| `structure-parser inspect-structure PATH` | Display heading structure tree |
| `structure-parser inspect-model PATH` | Display article/unit/component classification |
| `structure-parser inspect-references PATH` | Display references and resolution states |
| `structure-parser inspect-diagnostics PATH` | Display diagnostics grouped by severity |
| `structure-parser transform-readiness PATH [--target dita]` | Evaluate transform-readiness preconditions |
| `structure-parser validate-contract PATH...` | Validate fixture files against expected behavior |

## Exit Codes

| Code | Condition |
|---|---:|
| `0` | No errors; warnings only in advisory mode |
| `1` | Parse errors or validation invalid in strict mode |
| `2` | Unsupported schema version or configuration error |
| `3` | Internal controlled failure |

## Project Structure

```
structured-markdown/
├── pyproject.toml
├── mkdocs.yml
├── model/                          # Authoritative JSON schemas
├── src/structure_parser/
│   ├── api.py                      # Public API: parse_file, parse_files
│   ├── cli.py                      # Typer CLI
│   ├── logging_config.py
│   ├── adapters/                   # Format-specific parsers
│   │   ├── markdown.py             # markdown-it-py adapter
│   │   └── html.py                 # lxml adapter
│   ├── contracts/                  # Pydantic boundary contracts
│   │   ├── config.py
│   │   ├── parsed_document.py
│   │   ├── parse_run_result.py
│   │   ├── diagnostics.py
│   │   ├── references.py
│   │   ├── structure.py
│   │   ├── structured_markdown.py
│   │   ├── validation.py
│   │   └── transform_readiness.py
│   ├── domain/                     # Enums, errors, diagnostic codes
│   ├── enrichment/                 # Semantic enrichment pipeline
│   ├── structured_markdown/        # Article/unit/component classifier
│   ├── validation/                 # JSON Schema validation
│   ├── readiness/                  # Transform-readiness evaluators
│   ├── resolution/                 # Reference resolvers
│   ├── repositories/               # File system and schema I/O
│   ├── serialization/              # JSON serialization
│   ├── reporting/                  # Human-readable reporters
│   ├── debug/                      # Debug inspector
│   └── application/                # Orchestrator and commands
├── tests/
│   ├── unit/                       # Individual model and service tests
│   ├── contract/                   # Fixture-based contract tests
│   ├── integration/                # End-to-end API and CLI tests
│   └── fixtures/                   # Markdown, HTML, and expected JSON
├── schemas/                        # Generated JSON Schema artifacts
│   ├── parser/v1/
│   └── structured_markdown/v1/
├── docs/                           # MkDocs documentation source
└── tools/                          # Schema generation and fixture scripts
```

## Open Questions (from SRS)

| ID | Question | Impact |
|---|---|---|
| OQ-R1 | Legacy Markdown/HTML output fields requiring compatibility | Blocks final `legacy_adapter.py` scope |
| OQ-R2 | Required structured Markdown JSON Schemas for MVP validation | Affects `model_validator.py` profile config |
| OQ-R3 | Required metadata and taxonomy fields per validation profile | Affects author diagnostics |
| OQ-R4 | CI performance thresholds | Affects benchmark gating |
| OQ-R5 | Path-redaction policy for reports | Affects diagnostic output |
