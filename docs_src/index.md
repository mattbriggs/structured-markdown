# Semantic Markdown

Structured Markdown is an open semantic layer for Markdown. A parser uses the standard as a semantic contract to parses constrained Markdown into a stable, validated object model with provenance, enabling reliable transformation into downstream systems such as RAG pipelines, JSON-LD, DITA, RSS/Atom, knowledge graphs, static sites, and structured documentation workflows.

The current project is focusing on a layered Python package that parses Markdown and rendered HTML into a normalized structured content hierarchy for validation, publishing transforms, and RAG ingestion.

The repository pipeline extends the file parser to nested Markdown content repositories. It discovers Markdown files, calls the parser once per file, writes parsed JSON outputs, writes a CSV inventory report, and optionally writes a log file.

`structure_parser` parses Markdown and HTML into a normalized, classified content model that downstream systems can process without re-reading the source. Plain Markdown is readable and writable by any tool, but it carries no semantic contract: a heading is a heading, a list is a list, and no machine can tell a procedure from a reference section without inspecting the prose. `structure_parser` closes that gap by reading the source, classifying every block against a defined hierarchy, validating the result against JSON schemas, and returning a versioned Pydantic contract alongside author-facing diagnostics that explain every classification decision.

## The Four-Level Hierarchy

`structure_parser` maps source content to an **Article → Unit → Component → Attribute** hierarchy defined by the JSON schemas in `model/`.

- **Article** is the whole document. It has a type (`howto`, `concept`, `reference`, `troubleshooting`, `overview`, `tutorial`, `quickstart`, `glossary`, `glossentry`, `topic`) and an information type derived from its constituent units.
- **Unit** is a major section, bounded by an H2 heading. Units have types: `introduction`, `prerequisites`, `procedure`, `concept`, `principle`, `process`, `fact`, `reference`, `troubleshooting`, `glossary`, `glossentry`, `link-nextstep`, `link-related`.
- **Component** is a block-level element within a unit: a paragraph (`compParagraph`), a fenced code block (`compBlockCode`), an ordered list (`compListOrdered`), a table (`compTable`), an alert blockquote (`compAlertNote`, `compAlertWarning`, `compAlertCaution`, `compAlertTip`, `compAlertImportant`).
- **Attribute** is an inline element within a component: text (`attText`), a link (`attLink`), bold (`attBold`), italic (`attItalic`), inline code (`attCode`), an image (`attImage`).

This hierarchy enables machine-processable output that carries structural guarantees. A downstream DITA exporter, RAG chunking pipeline, or Schema.org annotator can traverse the `StructuredContent` model and make structural decisions — chunk boundaries, metadata extraction, element mapping — without content inspection.

## Two Classification Layers

`structure_parser` applies two independent classification systems to every article:

**Robert Horn information types** classify what kind of information a unit contains:

- `concept` — an explanation of what something is
- `procedure` — a sequence of steps to accomplish a goal
- `process` — a description of how a system operates
- `principle` — a rule or guideline governing behavior
- `fact` — a datum or reference item
- `structure` — a description of parts, relationships, or organization
- `classification` — a grouping or taxonomy of related things
- `mixed` — units of more than one type (applied at the article level when units disagree)
- `unknown` — content that could not be classified

The current runtime enum implements `concept`, `procedure`, `process`, `principle`, and `fact`, with `mixed` and `unknown` as parser states. The `structure` and `classification` types are reserved model-expansion targets for future schema work.

**DITA 1.3 topic types** classify the document's publishing intent: `topic`, `concept`, `howto`, `reference`, `troubleshooting`, `glossary`, `glossentry`. These map from the article's `articleType` front matter field and drive which schema in `model/articles/` is used for validation.

## Quick Start

Install the package:

```bash
pip install structure-parser
```

Parse a Markdown file and inspect its classification:

```bash
structure-parser parse my-article.md
structure-parser inspect-model my-article.md
structure-parser inspect-diagnostics my-article.md
```

Use the Python API:

```python
from structure_parser import parse_file

doc = parse_file("my-article.md")
print(doc.title)
print(doc.structured_content.article_type)

for unit in doc.structured_content.content:
    print(f"  {unit.unit_type.value}: {unit.title}")

if doc.has_errors:
    for d in doc.diagnostics:
        print(f"[{d.severity.value}] {d.code}: {d.message}")
```

## Diagnostic Code Categories

`structure_parser` emits diagnostics with stable `SP-NNN` codes in six categories:

- **SP-00x** — parse errors: file not found (SP-001), unsupported format (SP-002), parse failed (SP-003)
- **SP-01x** — metadata errors: malformed front matter (SP-010), front matter absent (SP-011)
- **SP-02x** — structural warnings: missing H1 (SP-020), heading level skipped (SP-021)
- **SP-03x** — schema errors: schema validation failed (SP-030), schema not found (SP-031)
- **SP-04x** — classification: unknown content (SP-040), article type unknown (SP-041)
- **SP-05x** — references: unresolved local reference (SP-050)
- **SP-06x** — transform readiness: readiness status (SP-060)
- **SP-09x** — internal: internal parser error (SP-099)

## MVP Scope

| Capability | Status |
|---|---|
| Markdown parsing (`.md`) | Complete |
| Rendered HTML parsing (`.html`) | Complete |
| YAML front matter extraction | Complete |
| Article / unit / component / attribute classification | Complete |
| JSON Schema validation against `model/` | Complete (advisory) |
| Reference classification | Complete |
| Local file reference resolution | Complete |
| Author-facing diagnostics (stable SP-NNN codes) | Complete |
| Transform-readiness evaluation (DITA, Schema.org, RAG) | Complete |
| CLI (9 subcommands, including `pipe`) | Complete |
| Python API (`parse_file`, `parse_files`, `run_pipeline`) | Complete |
| Repository pipeline for nested Markdown folders | Complete |
| DITA/XML parsing | Deferred (A-004) |
| Complex conref/keyref resolution | Deferred (A-005) |

## Key Links

- [Getting Started](getting-started.md) — installation, first parse, CLI walkthrough, Python API
- [Background: Why Markdown Is Not Semantic](concept/markdown-semantics.md) — the design rationale
- [Background: Parsing Approaches](concept/parsing-approaches.md) — AST, BNF, and schema mapping compared
- [Background: Comparison with Similar Tools](concept/comparison.md) — DITA, Pandoc, Vale, Markdoc, and more
- [Architecture Overview](architecture/overview.md) — layer contracts and data flow
- [User Guide: CLI Reference](user-guide/cli.md) — all nine subcommands with options
- [User Guide: Diagnostics](architecture/diagnostics.md) — SP-NNN codes and remediation
- [Model Reference](schemas/structured-markdown-v1.md) — Article → Unit → Component → Attribute schemas
- [API Reference](api/index.md) — `parse_file`, `parse_files`, `ParsedDocument`, `ParserConfig`
