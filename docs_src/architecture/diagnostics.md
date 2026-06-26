# Diagnostics

Every issue detected during parsing is emitted as a `Diagnostic` with a stable SP-NNN code, a severity level, a category, a human-readable message, and remediation guidance. Authors and tooling can act on diagnostic output without reading source code — the code alone identifies the problem class, and the remediation field tells the author exactly what to fix.

## The Diagnostic Contract

Each `Diagnostic` object carries the following fields:

| Field | Type | Meaning |
|---|---|---|
| `code` | `str` | Stable SP-NNN identifier (e.g., `"SP-020"`) |
| `severity` | `str` | `"error"`, `"warning"`, `"info"`, or `"debug"` |
| `category` | `str` | Problem class (see categories below) |
| `message` | `str` | Short, human-readable description of the problem |
| `detail` | `str \| None` | Extended explanation or raw error text |
| `remediation` | `str \| None` | Author-facing guidance on how to fix the issue |
| `provenance_status` | `str \| None` | `"available"`, `"partial"`, or `"unavailable"` |
| `source_path` | `str \| None` | Absolute path to the source file |
| `start_line` | `int \| None` | First source line of the problem (1-indexed) |
| `end_line` | `int \| None` | Last source line of the problem (1-indexed) |

Severity controls how the diagnostic affects `ParsedDocument.has_errors`: only `"error"` diagnostics set `has_errors` to `True`. Warning and info diagnostics are reported but do not block callers that gate on `has_errors`.

## Diagnostic Categories

Categories group diagnostics by problem domain. Each SP-NNN code belongs to exactly one category:

| Category | Meaning |
|---|---|
| `parse_error` | The adapter could not read or tokenize the source |
| `metadata_error` | Front matter is malformed or absent |
| `structural_warning` | The heading hierarchy violates authoring conventions |
| `authoring_violation` | The content does not conform to the schema |
| `reference_error` | A link or image reference cannot be resolved |
| `schema_error` | A JSON schema file is missing or incompatible |
| `unknown_classification` | Content could not be mapped to a known type |
| `transform_readiness` | A downstream transform target is blocked or degraded |
| `internal_error` | An unexpected exception occurred inside the parser |

## SP-NNN Code Table

| Code | Severity | Category | Meaning |
|---|---|---|---|
| SP-001 | error | parse_error | Source file not found |
| SP-002 | error | parse_error | Unsupported source format |
| SP-003 | error | parse_error | Parse failed |
| SP-010 | warning | metadata_error | Malformed front matter |
| SP-011 | info | metadata_error | Front matter absent |
| SP-020 | warning | structural_warning | Missing H1 title |
| SP-021 | warning | structural_warning | Heading level skipped |
| SP-030 | warning | authoring_violation | Schema validation failed |
| SP-031 | error | schema_error | Schema file not found |
| SP-032 | error | schema_error | Unsupported schema version |
| SP-040 | info | unknown_classification | Content classified as unknown |
| SP-041 | warning | unknown_classification | Article type undetermined |
| SP-050 | warning | reference_error | Unresolved local reference |
| SP-060 | info | transform_readiness | Transform readiness status |
| SP-099 | error | internal_error | Internal parser error |

## DiagnosticFactory

`DiagnosticFactory` is a class with 15 class methods, one per SP-NNN code. Each method pre-fills the `severity`, `category`, and `remediation` fields so that call sites only need to supply the context-specific `message`, `detail`, `source_path`, and line numbers. This eliminates the risk of a call site accidentally assigning the wrong severity or category to a known code.

For example, `DiagnosticFactory.sp_020(source_path, start_line)` returns a `Diagnostic` with `code="SP-020"`, `severity="warning"`, `category="structural_warning"`, and a pre-written remediation telling the author to add an H1 heading at the top of the document. Call sites never construct `Diagnostic` objects directly; they always call a factory method. This makes it straightforward to find every location in the codebase that emits a particular code by searching for the factory method name.

## Advisory vs. Strict Mode

The `validation_mode` field in `ParserConfig` controls how the Validation layer reports failures. In advisory mode (the default), schema validation failures produce SP-030 warnings; the pipeline continues and returns a `ParsedDocument` regardless of whether the content conforms to the schema. In strict mode, validation failures produce SP-099 errors instead, which set `has_errors` to `True` on the resulting `ParsedDocument`. Callers that gate on `has_errors` will treat a strict-mode validation failure as a hard stop.

Advisory mode is the right default for authoring workflows where partial documents are common and authors need feedback without a hard failure. Strict mode is appropriate for CI pipelines and publishing gates where only fully valid documents should proceed.

## How Diagnostics Are Used

`ParsedDocument` exposes three properties that make diagnostic-driven decisions concise: `has_errors` (bool), `error_count` (int), and `warning_count` (int). These properties aggregate across all diagnostics on the document regardless of which layer emitted them, so a caller does not need to filter the `diagnostics` list manually.

Two CLI commands surface diagnostics directly:

- `inspect-diagnostics` — prints all diagnostics for one or more parsed files, with optional filtering by severity or code.
- `validate-markdown` — parses a file, runs schema validation, and exits with a non-zero status code if `has_errors` is `True`. This command is designed for use in CI pipelines.
