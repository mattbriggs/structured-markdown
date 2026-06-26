# Layer Reference

The pipeline is divided into five layers, each with a bounded responsibility and a typed contract at its boundary. Understanding what each layer receives, what it produces, and what diagnostics it emits is the starting point for extending, debugging, or replacing any part of the system.

## Adapters Layer

The Adapters layer receives a file path and a `ParserConfig` and returns a `RawParseModel`. Its only job is to read source bytes and translate them into a normalized, format-agnostic list of `RawNode` objects alongside any front matter found in the file. The adapter does not interpret the document's meaning; it preserves source order and line numbers so that every downstream layer can trace content back to its origin.

Two concrete adapters are implemented:

- **Markdown adapter** — uses `markdown-it-py` to tokenize the source. The adapter converts the token stream into a flat list of `RawNode` objects, mapping each token type (`heading_open`, `fence`, `inline`, etc.) to a `node_type` string and capturing `start_line` and `end_line` from the token metadata. Front matter is extracted by the `mdit_py_plugins.front_matter` plugin before tokenization, which strips the YAML block and makes it available as a dict on `RawParseModel.front_matter`.
- **HTML adapter** — uses `lxml` to parse the source into an element tree and then traverses the tree depth-first, emitting a `RawNode` for each element. Because `lxml` does not always expose source line numbers for every element type, some nodes carry only a partial line position, which the provenance system records as `partial` status.

Both adapters satisfy the same adapter protocol: any class that implements `parse(source: str, path: str) -> RawParseModel` is a valid adapter. The `AdapterRegistry` maps source format strings (e.g., `"markdown"`, `"html"`) to adapter instances and raises SP-002 if no adapter is registered for a requested format. DITA XML adapter support is deferred to milestone A-004.

## Enrichment Layer

The Enrichment layer receives a `RawParseModel` and produces the metadata, heading structure, and reference inventory fields of the eventual `ParsedDocument`. It is organized as four sequential stages, all orchestrated by `semantic_enricher.py`.

**Stage 1 — Metadata extraction** (`metadata_extractor.py`): Reads the `front_matter` dict from the `RawParseModel`. If the dict is present and parseable, the extractor populates `ParsedDocument.metadata`. If the YAML block is present but malformed, it emits SP-010 (malformed front matter). If the block is absent entirely, it emits SP-011 (front matter absent, informational).

**Stage 2 — Structure building** (`structure_builder.py`): Walks the `RawNode` list looking for heading nodes, then builds a `DocumentStructure` — a tree of heading objects with their levels, text, and line positions. If the document has no H1 heading, the builder emits SP-020 (missing H1 title). If a heading level is skipped (for example, an H1 followed immediately by an H3 with no H2), the builder emits SP-021 (heading level skipped) for each gap detected.

**Stage 3 — Reference classification** (`reference_classifier.py`): Walks the `RawNode` list recursively, visiting inline nodes nested inside block nodes. It extracts every link href and image src as a `Reference` object with `ref_type` (`link` or `image`), `href`, and `text`. All references start in `not_attempted` state.

**Stage 4 — Reference resolution** (optional, `LocalFileResolver`): When `ParserConfig.resolve_local_references` is `True`, the resolver attempts to resolve each reference with a relative path against the source file's directory. Successfully resolved paths are written to `Reference.resolved_path` and the state is updated to `resolved`. External URLs are marked `unsupported`. References that cannot be found on disk emit SP-050 (unresolved local reference).

`semantic_enricher.py` calls all four stages in order and merges their diagnostics into a single list before handing control back to the orchestrator.

## Classification Layer

The Classification layer receives the `RawParseModel` and the metadata extracted in the enrichment stage, then produces a `StructuredContent` object. It is responsible for imposing the Structured Markdown content model on the flat node list. Three components work in sequence:

**Classifier** (`classifier.py`): Splits the `RawNode` list at H2 heading boundaries, treating each H2 and the nodes that follow it as a `Unit`. The classifier infers the `UnitType` from the heading title text using keyword matching (for example, a heading containing "Prerequisites" maps to `unitPrerequisites`). The overall article type is inferred from document-level metadata or the H1 title. If the article type cannot be determined, the classifier emits SP-041 (article type undetermined).

**Component mapper** (`component_mapper.py`): Iterates over each block-level `RawNode` within a unit and maps it to a `ComponentType`. A fenced code block becomes `compCodeBlock`; an unordered list becomes `compBulletList`; a paragraph becomes `compParagraph`. Nodes that match no known component type are mapped to `compUnknown` and emit SP-040 (content classified as unknown, informational).

**Attribute mapper** (`attribute_mapper.py`): Iterates over inline `RawNode` objects within each component and maps them to `AttributeType` values. A bold inline becomes `attEmphasisStrong`; an inline code span becomes `attCodeInline`. Unrecognized inline types are mapped to `attUnknown` and emit SP-040.

Unknown content is never discarded. The `artUnknown`, `unitUnknown`, `compUnknown`, and `attUnknown` sentinel values preserve all content in the output so that downstream systems can inspect or report on unclassified material rather than silently losing it.

## Validation Layer

The Validation layer receives the `StructuredContent` as a serialized Python dict and validates it against the JSON schemas stored in `model/articles/`. It returns a `ModelValidationResult` with a `valid` flag and any validation diagnostics.

The validator uses `jsonschema.Draft7Validator` with a pre-built schema store. At startup, `SchemaRepository` loads every `.schema.json` file in `model/articles/` and registers each one under three keys: its `file://` URI, its bare filename, and its `$id` value. Pre-loading the store avoids repeated file I/O during batch runs and allows cross-schema `$ref` chains to resolve without network access.

Validation mode controls how failures are reported:

- **Advisory mode** (default, `validation_mode = "advisory"`): Validation failures produce SP-030 warnings. The `ParsedDocument` is returned to the caller regardless of validation outcome.
- **Strict mode** (`validation_mode = "strict"`): Validation failures produce SP-099 errors, which set `ParsedDocument.has_errors` to `True`. Callers that check `has_errors` before processing will treat the document as unpublishable.

A known limitation affects cross-directory `$ref` chains that use bare `$id` filenames as reference targets. The `jsonschema` `RefResolver` does not always follow bare-filename references across directory boundaries, which can cause validation to produce SP-030 warnings in strict mode rather than raising a clean error. This behavior is documented in issue V-007.

## Readiness Layer

The Readiness layer receives the enriched `ParsedDocument` and evaluates it against three downstream transformation targets, returning a `TransformReadiness` that contains one `TargetReadiness` object per target. Each `TargetReadiness` carries a `status` (`ready`, `blocked`, or `degraded`), a list of human-readable `reasons`, and a `missing` list of fields or conditions required to reach `ready`.

Three evaluators run independently:

- **DitaReadinessEvaluator**: Checks that the document has a non-empty title, that the article type is not `artUnknown`, and that the article type maps to a supported DITA topic type (`concept`, `task`, `reference`, or `glossentry`). Any failing check sets status to `blocked`, because DITA transformation requires all three conditions.
- **SchemaOrgReadinessEvaluator**: Checks that the document has a title and a `description` metadata field. A missing description degrades status to `degraded` rather than blocking, because Schema.org markup can be emitted without it — but the result is less useful.
- **RagIngestionReadinessEvaluator**: Checks that the document has a title, that the `StructuredContent` contains at least one `Unit`, and that no SP-001, SP-002, or SP-003 parse errors are present. Parse errors block RAG ingestion because the content cannot be trusted to be complete.

All three evaluators emit SP-060 diagnostics (informational) that describe the readiness outcome, making it possible to surface readiness results through the standard diagnostic reporting pipeline alongside authoring and structural issues.
