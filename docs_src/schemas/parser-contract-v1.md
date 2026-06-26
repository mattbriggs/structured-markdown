# Parser Contract v1

## Overview

The four JSON Schema artifacts in `schemas/parser/v1/` define the stable v1 output contract for the `structure_parser` package. They are generated automatically from the Pydantic contract models by running:

```bash
python tools/generate_json_schemas.py
```

These schemas are checked into version control so that downstream tools — IDEs, validators, code generators, and data pipelines — can consume and validate parser output without a Python dependency. They follow JSON Schema Draft 7.

## ParsedDocument.schema.json

`ParsedDocument.schema.json` is the primary output contract. It describes the object returned by `parse_file()` and each element of `ParseRunResult.documents`.

**Required fields**: `source_path` (string), `source_format` (enum: `"markdown"` | `"html5"` | `"unknown"`).

**Optional top-level fields**:

| Field | JSON Type | Description |
|---|---|---|
| `schema_version` | string | Always `"1"` in this release |
| `provenance` | object | Content hash, parse timestamp, adapter version |
| `metadata` | object | Front matter fields; additional properties allowed |
| `title` | string or null | Document title from H1 or front matter |
| `structure` | object or null | Heading outline tree |
| `structured_content` | object or null | Classified content hierarchy (see Article schema) |
| `references` | array | `Reference` objects for all links and images |
| `diagnostics` | array | `Diagnostic` objects for all issues found |
| `validation` | object or null | `ModelValidationResult` from schema validation |
| `readiness` | object or null | `TransformReadiness` with per-target status |

**Minimal JSON example**

```json
{
  "schema_version": "1",
  "source_path": "/docs/install.md",
  "source_format": "markdown",
  "title": "Installing the Package",
  "metadata": { "author": "eng-team" },
  "references": [],
  "diagnostics": []
}
```

The full schema includes `$defs` for all referenced types — `Diagnostic`, `Reference`, `StructuredContent`, `Unit`, `Component`, `Attribute`, `ModelValidationResult`, `TransformReadiness`, `TargetReadiness`, `DocumentProvenance`, `SourceSpan`, `DocumentStructure`, and all enums — so the file is self-contained and can be used as a standalone validator.

## ParseRunResult.schema.json

`ParseRunResult.schema.json` describes the object returned by `parse_files()`.

**Top-level fields**:

| Field | JSON Type | Description |
|---|---|---|
| `schema_version` | string | Always `"1"` |
| `documents` | array | Array of `ParsedDocument` objects, one per input path |
| `run_diagnostics` | array | Diagnostics that apply to the run as a whole rather than any single file |
| `stats` | object | `ParseStats` object (required) |

**The stats object**:

| Field | JSON Type | Description |
|---|---|---|
| `file_count` | integer | Number of input paths processed |
| `error_count` | integer | Total error-severity diagnostics across all documents |
| `warning_count` | integer | Total warning-severity diagnostics across all documents |
| `duration_ms` | number | Wall-clock parse time in milliseconds |

**Minimal JSON example**

```json
{
  "schema_version": "1",
  "documents": [],
  "run_diagnostics": [],
  "stats": {
    "file_count": 3,
    "error_count": 0,
    "warning_count": 2,
    "duration_ms": 47.3
  }
}
```

## Diagnostic.schema.json

`Diagnostic.schema.json` defines a single issue record. Diagnostics appear in `ParsedDocument.diagnostics`, `ModelValidationResult.diagnostics`, and `TargetReadiness.diagnostics`.

**Required fields**: `code` (string), `severity` (enum), `category` (enum), `message` (string).

**Optional fields**:

| Field | JSON Type | Description |
|---|---|---|
| `schema_version` | string | Always `"1"` |
| `detail` | string | Additional context about the issue |
| `remediation` | string | Suggested corrective action |
| `provenance_status` | enum | `"available"` \| `"partial"` \| `"unavailable"` |
| `source_path` | string or null | File where the issue was found |
| `start_line` | integer or null | 1-based line number; minimum 1 |
| `end_line` | integer or null | 1-based end line; minimum 1 |

**Severity enum values**: `"error"`, `"warning"`, `"info"`, `"debug"`.

**Category enum values**: `"parse_error"`, `"metadata_error"`, `"structural_warning"`, `"authoring_violation"`, `"reference_error"`, `"schema_error"`, `"unknown_classification"`, `"transform_readiness"`, `"internal_error"`.

## Reference.schema.json

`Reference.schema.json` defines a single link or image reference extracted from the source document.

**Required fields**: `ref_type` (string: `"link"` or `"image"`), `href` (string).

**Optional fields**:

| Field | JSON Type | Description |
|---|---|---|
| `schema_version` | string | Always `"1"` |
| `text` | string or null | Link text or image alt text |
| `alt_text` | string or null | Image alt text (also carried on `text` for images) |
| `state` | enum | `"not_attempted"` \| `"resolved"` \| `"unresolved"` \| `"unsupported"` |
| `resolved_path` | string or null | Absolute filesystem path when `state == "resolved"` |
| `source_path` | string or null | Source file containing the reference |
| `start_line` | integer or null | 1-based line number; minimum 1 |
| `end_line` | integer or null | 1-based end line; minimum 1 |

## Regenerating the Schemas

Run the following command from the repository root after any change to a contract model:

```bash
python tools/generate_json_schemas.py
```

The tool calls `model_json_schema()` on each Pydantic model and writes the result to the appropriate `schemas/parser/v1/` or `schemas/structured_markdown/v1/` file. Commit the output alongside the Python change. When a breaking change requires a version bump, update the tool to write to a `v2/` directory and leave `v1/` in place for consumers that have not yet migrated.
