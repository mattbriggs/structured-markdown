# Structure-Aware Parser

A layered Python package that parses Markdown and rendered HTML into a normalized structured content hierarchy for validation, publishing transforms, and RAG ingestion.

## What It Does

The parser converts:

- **Markdown source** (`.md`) and **rendered HTML** (`.html`) into a structured JSON document
- The structure maps to an **Article -> Unit -> Component -> Attribute** hierarchy
- Outputs are validated against **JSON Schemas** defined in the `model/` directory
- Author-facing **diagnostics** explain what needs fixing and why

## MVP Scope

- [x] Markdown parsing
- [x] Rendered HTML parsing
- [x] Structured Markdown classification
- [x] JSON Schema validation
- [x] Reference classification
- [x] Author diagnostics
- [x] CLI commands
- [x] Python API
- [ ] DITA/XML parsing (deferred — A-004)
- [ ] Full conref/keyref resolution (deferred — A-005)

## Quick Start

```bash
pip install structure-parser
structure-parser parse README.md
structure-parser inspect-model README.md
```

See [Getting Started](getting-started.md) for full setup instructions.
