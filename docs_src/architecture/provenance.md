# Provenance

Provenance is the record of where parsed content came from. The pipeline tracks two granularities of origin: document-level provenance (which file was parsed, when, and by which adapter) and node-level provenance (which lines of that file produced a specific unit, component, or attribute). Together they enable cache invalidation, IDE click-to-source navigation, and audit trails that survive round-trips through serialization.

## DocumentProvenance

`DocumentProvenance` is attached to every `ParsedDocument` and carries four fields:

| Field | Type | Meaning |
|---|---|---|
| `content_hash` | `str` | SHA-256 hex digest of the raw source bytes |
| `parse_timestamp` | `str` | ISO 8601 UTC timestamp of when parsing completed |
| `adapter_version` | `str` | Version string of the adapter that processed the file |
| `schema_version` | `str` | Contract version in use at parse time |

The `content_hash` field is the primary mechanism for cache invalidation. A downstream system that caches `ParsedDocument` objects can compare the stored `content_hash` against a freshly computed hash of the source file before deciding whether to re-parse. If the hashes match, the cached document is still valid; if they differ, the file has changed and must be re-parsed. This check is O(1) in the size of the document model and requires only one SHA-256 pass over the raw bytes.

## SourceSpan

`SourceSpan` is attached to individual `Unit`, `Component`, and `Attribute` objects in the classification output. It carries the precise source location of each classified element:

| Field | Type | Meaning |
|---|---|---|
| `source_path` | `str` | Absolute path to the originating source file |
| `start_line` | `int \| None` | First source line of the element (1-indexed) |
| `end_line` | `int \| None` | Last source line of the element (1-indexed) |
| `provenance_status` | `str` | `"available"`, `"partial"`, or `"unavailable"` |

## ProvenanceStatus Values

The `provenance_status` field communicates what is known about the source location:

- **`available`** — both `source_path` and line numbers are known. The element can be mapped back to a precise range in the source file.
- **`partial`** — `source_path` is known but line numbers are `None`. The element can be attributed to a file but not to specific lines.
- **`unavailable`** — neither path nor line numbers are known. This occurs when content is synthesized by the enrichment layer rather than read from a source node.

## Why Provenance Matters

Provenance serves three concrete use cases. First, cache invalidation: `content_hash` allows any system that stores parsed output to detect file changes without re-parsing, which is critical for large documentation sets processed in CI. Second, IDE integration: tools that consume `ParsedDocument` objects can use `SourceSpan.start_line` and `end_line` to implement click-to-source navigation, highlighting the exact lines that produced a given unit or component. Third, audit trails: `parse_timestamp` and `adapter_version` together make it possible to reproduce a parse run exactly by identifying which version of the adapter processed the file and when, which matters for debugging regressions introduced by adapter upgrades.

## HTML Adapter Limitation

The HTML adapter uses `lxml` to traverse the element tree, and `lxml` does not expose source line numbers for every element type. Elements for which `lxml` returns no line information produce `SourceSpan` objects with `provenance_status = "partial"` and `start_line = None`. This means HTML documents have lower provenance fidelity than Markdown documents, where `markdown-it-py` provides line numbers for nearly every token. Future adapter versions may improve this by using an alternative HTML parser that preserves more position metadata.
