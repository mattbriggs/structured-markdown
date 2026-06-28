# B1 Parse Assessment Implementation Update

## Purpose

This implementation note converts the findings in [`design/assess/2026-06-29-b1-assess/assess.md`](assess/2026-06-29-b1-assess/assess.md) into a generic parser improvement plan.

The goal is not to tune the parser for the assessed Azure Stack content set. The goal is to make the parser better at consuming arbitrary, non-DITA Markdown and triaging it into useful article, unit, component, and readiness structures.

## Assessment Summary

The B1 assessment shows that the parser is now a strong loss-preserving structural parser. All 31 assessed files produced `ParsedDocument` output with title, metadata, structured content, references, diagnostics, and readiness records. The parser produced 169 units, 133 of which were known unit types, for a 78.7% known-unit rate.

The output is already useful for generic XML and metadata-rich RAG chunking. Unit boundaries are generally good chunk boundaries, references and image references are captured, and unknown content is preserved rather than dropped.

The remaining issue is semantic triage. The parser produced a healthier article-type mix than earlier runs, but it still needs a more conservative default for generic Markdown. Non-DITA Markdown should normally become `topic` unless the document structure provides strong evidence for a specialized article type.

The assessment also found that all files had `validation: null`. That means DITA readiness should not be interpreted as standards compliance. DITA readiness needs to distinguish minimum transform prerequisites from validated, publication-safe DITA confidence.

## Design Constraints

The parser must consume generic Markdown. The implementation may learn from the assessed batch, but it must not hard-code Azure Stack, Microsoft Docs, product names, cloud-service names, or specific filenames.

Classifier behavior must be based on reusable Markdown evidence:

- metadata key/value evidence
- heading text patterns
- section construction
- unit distribution
- component density
- procedure density
- reference density
- validation status
- diagnostics and triage status

The parser must remain loss-preserving. Unknown article, unit, component, or attribute classification should keep the source content in the output model, emit diagnostics, and remain usable for XML and RAG.

The parser must keep classification and compliance separate. The classifier can report best-effort semantic type and confidence. The validator determines schema compliance. The readiness layer reports whether a downstream transform can safely proceed.

## Core Triage Rule

For non-DITA Markdown, `topic` is the conservative article default.

The parser should promote from `topic` to a specialized article type only when evidence is strong:

| Article type | Promotion evidence |
|---|---|
| `howto` | Clear procedural sections, ordered steps, command sequences, prerequisites plus steps, or repeated procedure units |
| `reference` | Reference-dominant content such as tables, lists, catalogs, support matrices, API/version notes, parameters, options, resource summaries, or compatibility data |
| `concept` | Explanatory content dominated by overview, background, architecture, how-it-works, or conceptual units |
| `troubleshooting` | Problem, symptom, cause, resolution, diagnostic, or repair-oriented sections |
| `glossary` / `glossentry` | Term-definition structure |

The parser should not promote a file to `howto` because it has a `Next steps` section, a few links, or one action-oriented heading. It should not promote a file to `reference` because it has some links. The whole article shape should matter.

## Current Implementation Context

The current classifier already has several useful pieces:

- `_MetadataEvidence`
- `_ArticleCandidateScore`
- `_UNIT_TITLE_MAP`
- `_ARTICLE_SIGNATURES`
- `_MIN_MARGIN`
- `_infer_article_type_from_metadata()`
- `_score_article_type()`
- topic fallback when specialized scores are weak

This update should refine that evidence model rather than replace it wholesale.

The important gap is that the current scorer still allows some specialized classifications without enough whole-document confidence. It also does not expose enough triage evidence in the output contract for later debugging, DITA fallback decisions, or RAG quality metadata.

## Implementation Plan

### 1. Add Article Triage Evidence to the Output Contract

Add a structured article triage summary to `StructuredContent.metadata` or a dedicated contract field if the model is ready for that change.

The triage summary should include:

- selected article type
- selected DITA type
- triage status
- confidence score
- candidate scores
- winning margin
- promotion rule used
- metadata evidence used
- unit evidence summary
- reason strings suitable for diagnostics or reports

Example shape:

```json
{
  "articleTriage": {
    "selected": "topic",
    "confidence": 0.72,
    "defaultApplied": true,
    "winningMargin": 2,
    "candidates": [
      {"articleType": "topic", "score": 8, "reason": "mixed known units"},
      {"articleType": "howto", "score": 6, "reason": "one procedure unit, insufficient dominance"},
      {"articleType": "reference", "score": 5, "reason": "table-heavy sections"}
    ],
    "evidence": [
      "metadata ms.topic=overview normalized as weak topic evidence",
      "procedure units present but not dominant",
      "reference units present but not dominant"
    ]
  }
}
```

This does not need to become part of the strict schema immediately. It can start as metadata so downstream reports and tests can inspect it without blocking the parser contract.

### 2. Make `topic` the Explicit Generic Markdown Default

Refine `_score_article_type()` so `topic` is selected when:

- at least two known unit types are present and no specialized type wins by margin
- metadata maps to generic values such as `article`, `guide`, `overview`, or `tutorial`, but construction evidence is mixed
- the document has meaningful structure but the specialized signatures conflict
- validation is absent and DITA output confidence is otherwise uncertain

`unknown` should be reserved for very low-evidence content: no title, no meaningful units, unsupported structure, or mostly unknown content with little recoverable semantic signal.

### 3. Add Specialized Promotion Gates

Add explicit promotion gates before returning a specialized article type.

For `howto`, require:

- at least one `procedure` unit, and
- either multiple procedure units, or procedure weight greater than non-procedure known-unit weight, and
- no strong reference/concept/principle majority.

For `reference`, require:

- at least one `reference` or `fact` unit, and
- reference/fact unit weight greater than procedure and concept/principle weight, or
- table/list/catalog/API/version density above a configured threshold.

For `concept`, require:

- concept/principle/process units to dominate, or
- metadata strongly indicates concept and body shape does not conflict.

If a specialized type fails its promotion gate, the result should fall back to `topic` when the document is otherwise structured.

### 4. Add Generic Section-Shape Evidence

The unit classifier should use more than heading text. It should combine heading evidence and body construction evidence.

Reusable section-shape signals:

| Signal | Possible unit evidence |
|---|---|
| Ordered list with imperative steps | `procedure` |
| Paragraph plus code block command sequence | `procedure` |
| Table-heavy section | `reference` or `fact` |
| Dense unordered list of options/resources | `reference` |
| Term-definition list | `glossary` / `glossentry` |
| Short explanatory prose | `concept` |
| Design guidance or tradeoff language | `principle` |
| Problem/solution/cause/remediation structure | `troubleshooting` |
| Link-only list | `link-related` or `link-nextstep` depending heading |

This must stay generic. A heading such as `Context and problem` should not be an Azure-specific rule; it is a reusable architecture-pattern signal that can contribute concept/problem evidence.

### 5. Improve Generic Heading Pattern Coverage

Expand heading patterns only when they represent common documentation semantics.

Candidate generic patterns:

| Pattern family | Example headings | Unit target |
|---|---|---|
| Reference data | `API version`, `Parameters`, `Options`, `Settings`, `Limits`, `Compatibility`, `Support matrix` | `reference` / `fact` |
| Catalog/gallery | `Examples`, `Samples`, `Templates`, `Resources`, `Catalog`, `Available providers` | `reference` / `link-related` |
| Architecture pattern | `Context and problem`, `Solution`, `When to use this pattern`, `Issues and considerations` | `concept` / `principle` / `topic` |
| Guidance | `Best practices`, `Recommendations`, `Design considerations`, `Security`, `Reliability` | `principle` |
| Concept | `Overview`, `Background`, `How it works`, `Architecture`, `Before you start` | `concept` / `introduction` / `prerequisites` |
| Procedure | `Create`, `Configure`, `Deploy`, `Install`, `Connect`, `Run`, `Test`, `Verify` with step-shaped body | `procedure` |

Action verbs should not classify a unit as `procedure` by themselves. They should be confirmed by ordered steps, command/code sequences, or another procedural construction signal.

### 6. Reduce Unknown Units Without Hiding Uncertainty

The B1 batch had 36 unknown units across 14 files. The update should reduce that count by classifying common generic section shapes, but unknown must remain available.

Unknown should remain the correct result when:

- section body is malformed or unsupported
- heading and body evidence conflict strongly
- component mapper cannot preserve the content accurately
- the section is structurally meaningful but not yet covered by a generic rule

Unknown units and components should carry reason metadata when practical:

```json
{
  "triage_status": "unknown",
  "metadata": {
    "unknownReason": "no_generic_unit_pattern_matched",
    "observedComponents": ["paragraph", "table", "list"]
  }
}
```

### 7. Make DITA Readiness Honest About Validation Absence

Update `DitaReadinessEvaluator` so missing validation is visible.

Recommended behavior:

| Validation state | DITA readiness effect |
|---|---|
| `valid: true` and no blocking diagnostics | `ready` |
| `valid: false` | `degraded` |
| `validation is None` | `degraded` or `not_attempted`, with explicit missing prerequisite |
| unknown article type | `blocked` or `degraded` depending output mode |
| known article type but low confidence | `degraded` |

The exact status can be configurable, but the readiness report must not imply validated DITA compliance when validation did not run.

Add a prerequisite message such as:

```text
Schema validation was not evaluated; DITA compliance is not proven
```

### 8. Preserve RAG Permissiveness, Add Quality Metadata

RAG readiness should remain more permissive than DITA readiness. A document can be useful for RAG when it has title, content, unit boundaries, source path, and no parse errors.

However, RAG chunks should carry quality metadata:

- article type
- article confidence
- unit type
- unit confidence
- triage status
- diagnostic codes
- validation state
- source path
- source span
- reference count
- image count

This lets downstream retrieval choose high-recall or high-confidence chunk subsets without losing content.

### 9. Keep Image Handling Generic

The B1 batch captured 47 image references across 15 files. The parser should keep image handling generic:

- preserve Markdown image and HTML `img` attributes
- record source path and alt text
- distinguish inline image, block image, and figure-like image context when possible
- report missing alt text as an accessibility quality signal
- expose local image resolution state when reference resolution runs

Do not add corpus-specific image rules. Image behavior should serve generic Markdown-to-XML, Markdown-to-DITA, and RAG provenance needs.

## Acceptance Criteria

The parser continues to parse arbitrary Markdown without requiring DITA-specific syntax.

Generic Markdown with mixed known units falls back to `topic` unless a specialized type wins by confidence margin and promotion gate.

A document with `Overview`, `Architecture`, `Considerations`, and `Next steps` does not classify as `howto` unless it also has dominant procedural sections.

A document with multiple procedure sections, ordered steps, prerequisites, and command sequences classifies as `howto`.

A document dominated by tables, parameter lists, version matrices, support matrices, option lists, or resource catalogs classifies as `reference` when reference evidence dominates.

A document with table/list reference sections plus procedural sections falls back to `topic` unless either procedure evidence or reference evidence clearly dominates.

Generic architecture-pattern headings are classified without hard-coding product names or filenames.

Unknown-unit diagnostics decrease on the B1 assessment set, but unknown content remains preserved and visible.

DITA readiness reports `degraded` or explicitly `not_attempted` when schema validation is absent.

RAG readiness remains `ready` for structurally parsed documents with no parse errors, while chunk metadata includes triage and diagnostic quality signals.

## Test Plan

Add unit tests for article promotion gates:

- mixed concept/reference/procedure content should become `topic`
- one `procedure` plus many reference/concept units should not become `howto`
- multiple procedure units plus prerequisites should become `howto`
- table-heavy and list-heavy reference documents should become `reference`
- ambiguous reference/procedure documents should become `topic`

Add unit tests for generic heading and section-shape evidence:

- `Parameters`, `Options`, `Compatibility`, and `API version` produce reference/fact evidence
- `Context and problem`, `Solution`, and `When to use this pattern` produce concept/principle/topic evidence
- action-verb headings require procedural body shape before becoming procedure units
- paragraph plus command code block can become procedure evidence
- link-only sections classify as link-related or next-step based on heading context

Add readiness tests:

- DITA readiness is `ready` only when title, article type, DITA mapping, and validation confidence are present
- DITA readiness is degraded or not attempted when validation is `None`
- RAG readiness remains ready for structured content with diagnostics but no parse errors

Add regression assessment tests using generic expectations, not fixture-specific assertions:

- known-unit rate should improve from the B1 baseline
- unknown-unit diagnostics should decrease
- article-type distribution should remain conservative
- `topic` should be the fallback for ambiguous generic Markdown
- DITA readiness should no longer imply schema compliance when validation is absent

## Implementation Sequence

1. Add article triage evidence metadata or contract support.
2. Refine `_score_article_type()` to apply explicit `topic` fallback and specialized promotion gates.
3. Add section-shape evidence helpers for procedure density, reference density, concept/principle density, and unknown reasons.
4. Expand heading patterns only with generic documentation semantics.
5. Add unknown reason metadata for units and components where practical.
6. Update `DitaReadinessEvaluator` to report validation absence as degraded or not attempted.
7. Extend RAG chunk metadata design to include confidence, diagnostics, validation state, references, and images.
8. Add focused unit tests and readiness tests.
9. Re-run the B1 assessment set and compare metrics against the current baseline.

## Expected Outcome

The parser should remain a generic Markdown parser, not a content-set-specific migration script.

The improved parser should preserve content as reliably as it does now, reduce unknown units through reusable documentation patterns, and produce more trustworthy article triage:

- `topic` for ordinary or mixed generic Markdown
- `howto` for truly procedural content
- `reference` for genuinely reference-dominant content
- `concept` for explanatory concept-dominant content

DITA readiness should become more honest. RAG chunking should remain permissive but carry quality metadata. XML transforms should continue to preserve unknowns explicitly so downstream systems can choose between broad content preservation and stricter semantic confidence.
