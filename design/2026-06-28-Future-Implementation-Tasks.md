# Future Implementation Tasks

## Purpose

This note records two implementation areas that are intentionally outside the current MVP but should be planned as follow-on work: a DITA XML transformer for parsed JSON repository output, and richer image handling across parsing, validation, and downstream publishing workflows.

## Task 1: Transform Parsed JSON Repository Output to DITA XML

The current project parses Markdown and HTML into a stable `ParsedDocument` / `StructuredContent` JSON contract and evaluates DITA transform readiness. It does not yet emit DITA XML. A future implementation should add a transformer that converts the normalized repository JSON output into DITA topic files and, where useful, DITA maps.

The transformer should consume the existing parser contract rather than re-reading Markdown. This keeps parsing, classification, validation, and publishing concerns separated: the parser produces the semantic model, and the DITA transformer serializes that model into XML.

### Scope

- Add a JSON/contract-to-DITA transformation layer.
- Support single-document transformation from `ParsedDocument`.
- Support repository-level transformation from pipeline JSON outputs.
- Map article types to DITA topic roots such as `topic`, `concept`, `task`, `reference`, `troubleshooting`, `glossary`, and `glossentry`.
- Map units and components into valid DITA body structures.
- Preserve provenance and diagnostics as optional comments, processing instructions, or sidecar reports.
- Emit degraded output only when readiness allows it and record any fallback mappings.
- Add CLI and Python API entry points for DITA export.

### Design Considerations

The transformer should honor the readiness model. A document with `dita:blocked` should not silently produce publishable XML. A document with `dita:degraded` may produce XML with generic containers or warnings, but the output should make that degradation visible to callers.

The transformer should be schema-aware but not duplicate parser validation. It should rely on the structured model for classification and use DITA validation as a final output check when a DITA toolchain is available.

Repository-level export should preserve relative source paths where possible. For example, a parsed output file for `guides/install.md` should produce a predictable DITA path such as `guides/install.dita`, with an optional map describing navigation order.

### Initial Acceptance Criteria

- A parsed `howto` document can be exported as a DITA task.
- A parsed `concept` document can be exported as a DITA concept.
- A parsed `reference` document can be exported as a DITA reference.
- Unknown or unsupported components are preserved in a safe fallback representation.
- The CLI can export one parsed JSON file or a directory of parsed JSON files.
- Tests cover ready, degraded, and blocked DITA readiness states.

## Task 2: Expand Image Handling

The current parser recognizes Markdown images and HTML `img` elements as inline `attImage` attributes. It records the image source, alt text, and a reference entry, and optional local reference resolution can mark image paths as `resolved` or `unresolved`. The project does not yet perform asset copying, image metadata inspection, accessibility validation, or DITA-specific image serialization.

Future image handling should treat images as first-class publishing assets while preserving the current inline attribute model.

### Scope

- Validate missing or empty image alt text with a dedicated diagnostic.
- Preserve image references in DITA output as `image` elements with appropriate `href`, `alt`, and placement.
- Resolve local image assets during repository export.
- Optionally copy image assets into the DITA output tree while preserving relative relationships.
- Track asset inventory for pipeline reports.
- Support image references inside paragraphs, lists, tables, and standalone image paragraphs.
- Add clear behavior for remote images, unsupported schemes, and missing local files.

### Design Considerations

Standalone Markdown images are currently represented as paragraph components containing an `attImage`. The future implementation should decide whether that is sufficient for all downstream targets or whether the structured model needs an explicit image/block media component.

Accessibility checks should distinguish decorative images from missing authoring data. If decorative images are supported, the model needs a way to represent author intent rather than treating every empty `alt` value as an error.

DITA export must account for context. An image inside prose may become an inline image, while a standalone paragraph image may be better serialized as a block image or figure. Captions are not currently modeled as a dedicated image feature, so caption support may require a new component or metadata convention.

Asset copying should be optional. Some publishing systems expect source-controlled asset paths to remain external, while others need a complete output directory containing XML and media files.

### Initial Acceptance Criteria

- The parser emits a diagnostic for non-decorative images with missing alt text.
- Pipeline reports include image counts and unresolved image references.
- DITA export serializes image attributes into valid image markup.
- Repository export can optionally copy local image assets into the output directory.
- Missing local image assets produce actionable diagnostics without stopping unrelated files from exporting.

## Open Questions

- Should DITA export operate directly from `ParsedDocument` objects, serialized JSON files, or both?
- Should image asset copying live inside the DITA exporter, the pipeline layer, or a separate asset manager?
- Should the model add a block-level image or figure component, or should image-as-inline-attribute remain the only representation?
- How should decorative images be represented in Markdown without introducing project-specific syntax?
