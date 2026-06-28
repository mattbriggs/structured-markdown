## Where you are

You are **past toy parser** and into **early working semantic infrastructure**. Annoying for everyone who wanted this to be merely a neat repo, but here we are.

The strongest signal: the parser is already doing the hard, boring, necessary part well. Your README says the tool maps Markdown into an **Article → Unit → Component → Attribute** hierarchy with Pydantic contracts, diagnostics, schema validation, and transform-readiness reports. That is not a weekend regex gremlin anymore; that is a real architecture. 

The architecture is also properly layered: adapters produce raw parse models, enrichment builds parsed documents, the structured Markdown classifier produces structured content, validation checks the model, and readiness evaluates downstream suitability. That separation is exactly what you need if this is going to become a stable semantic contract rather than “yet another Markdown parser,” because apparently civilization demanded a thousand of those. 

Your current weakness is not parsing. It is **semantic overconfidence**.

The assessment says the parser preserved all six sample files structurally, produced titles, metadata, units, references, diagnostics, validation output, and readiness records. That is good. But all six files were classified as `howto`, while several source documents were closer to `conceptual`, `overview`, `article`, or `reference`. The readiness flags said things like DITA/RAG ready while schema validation failed. That means your parser is currently too willing to say, “Sure, this is a how-to,” because it saw a `Next steps` section and got excited like a golden retriever with a clipboard.

## The core diagnosis

You have three systems that are not yet fully aligned:

1. **The structural parser** is doing well.
2. **The classifier** is too eager and too brittle.
3. **The validator/readiness layer** is not yet honest enough about uncertainty.

The current classifier code confirms the issue. It uses a heading keyword map, then simple article signatures with required/preferred/excluded units. `howto` requires a procedure and gives preferred weight to `prerequisites`, `introduction`, `link_nextstep`, and `link_related`.  

Then article type selection is basically: metadata first, otherwise infer from units. If a candidate wins outright by score, it becomes the article type; if there are two or more known unit types and no winner, it falls back to `topic`; otherwise it returns `unknown`.  

That is a reasonable MVP. It is also exactly where the false positives come from. The classifier sees a little procedure-shaped evidence and promotes the whole article to a specialized type. The roadmap should therefore not be “add more keywords” as the main strategy. That way lies madness, followed by a YAML file the size of Nebraska.

The next stage is to make the parser **evidence-driven, conservative, inspectable, and corpus-tested**.

---

# Roadmap to season the parser

## Phase 1: Make semantic confidence explicit

This is the most important next move.

Right now, the parser emits `triage_status`, but the decision does not expose enough evidence. The contracts already include `triage_status` on attributes, components, units, and structured content, which is a strong foundation.   

Add explicit classifier evidence objects:

```text
MetadataEvidence
HeadingEvidence
ConstructionEvidence
UnitEvidence
ArticleCandidateScore
ArticleTriageDecision
```

Each article decision should preserve:

```json
{
  "selected_article_type": "topic",
  "triage_status": "ambiguous",
  "confidence": 0.62,
  "scores": {
    "howto": 7,
    "concept": 6,
    "reference": 5,
    "topic": 4
  },
  "reasons": [
    "procedure evidence present",
    "reference table evidence present",
    "metadata suggests conceptual",
    "howto did not meet dominance margin"
  ]
}
```

The point is not just better classification. It is **debuggability**. When a document is wrong, you need to know whether the failure came from metadata normalization, heading interpretation, body shape, schema mismatch, or readiness policy.

### Done when

A developer can run:

```bash
structure-parser inspect-triage some-file.md
```

And see why the article and each unit were classified.

---

## Phase 2: Replace “winner takes article” with scored article triage

Your implementation note is exactly right here. The article type should not be selected merely because one unit looks procedural.

Add minimum thresholds:

```text
min_score = 6
min_margin = 3
dominance_ratio = 0.55 or 0.60
```

For `howto`, require:

```text
at least one procedure unit
AND
procedure evidence outweighs non-procedure evidence
AND
the win clears the confidence margin
```

`Next steps` should be nearly neutral. It is navigation, not article identity. In Microsoft-style docs, almost everything has `Next steps`, because apparently every page must end by shoving the reader into another hallway.

### Suggested article selection policy

| Evidence state | Article type |
|---|---|
| Strong declared metadata and no contradiction | Declared type |
| Strong metadata but contradictory body | Declared type, degraded confidence |
| Procedure-dominant body | `howto` |
| Concept/process/principle-dominant body | `concept` or `overview` |
| Fact/reference/table/API-dominant body | `reference` |
| Mixed known units, no clear winner | `topic` |
| Mostly unknown units | `unknown` |

This is the philosophical shift: **`topic` is not failure. `topic` is the correct generic fallback.**

`unknown` should mean “I cannot safely interpret this.” `topic` should mean “I can structure this, but I should not pretend it is a specialized information type.”

---

## Phase 3: Improve unit classification using body shape, not just headings

The current unit classifier relies first on heading keywords, then a simple body-shape heuristic: ordered lists or code-only sections can become procedures. 

That is a good start, but now you need richer construction evidence.

Add signals like:

```text
has_ordered_steps
has_imperative_step_markers
has_table_dominance
has_definition_list_shape
has_link_list_dominance
has_code_plus_explanation
has_warning_or_note_density
has_h3_subsections
has_parameter_table
has_version_matrix
has_comparison_table
```

Then separate heading suggestion from body confirmation:

```text
Heading: "API version" → reference/fact evidence
Body: table-heavy → confirms reference/fact
Body: ordered list → possible procedure conflict
Decision: reference/fact unless procedure dominance is strong
```

This matters because real Markdown is often rhetorically mixed. A heading like “Create your first VM” might introduce conceptual guidance, a table, a link list, and then one task-like paragraph. That is not automatically a procedure unit. Human-authored docs are little compost piles of intent. Charming species.

---

## Phase 4: Treat pre-H2 content as `introduction` when safe

Your splitter already creates a section with `heading_node = None` for preamble content. 

Right now, that often becomes unknown. That is fixable and should be an early win.

Rule:

```text
If the pre-H2 section has paragraphs, images, applies-to notes, brief lists, or summary text,
and no strong conflicting signal,
classify as introduction.
```

This will reduce noisy `unitUnknown` diagnostics and improve RAG chunk metadata without pretending to understand too much.

### Do not overdo it

If pre-H2 content is weird, code-heavy, malformed, or structurally chaotic, keep it unknown. The parser should remain loss-preserving and humble. Humility in software: rare, medicinal, generally ignored until production.

---

## Phase 5: Align runtime model, JSON Schema, and readiness

This is the second major roadblock.

Your README says JSON Schema validation is complete but advisory.  That is fine for MVP, but for this project’s actual value proposition, schema validation is not decoration. It is the semantic contract.

Right now, your assessment shows an uncomfortable split:

```text
readiness: DITA ready / RAG ready
validation: false
```

That means “can be transformed somehow” and “is semantically compliant” are being collapsed too loosely.

Fix this by making readiness statuses more precise:

| Status | Meaning |
|---|---|
| `ready` | Valid, confident, transformable |
| `degraded` | Transformable, but schema-invalid or low-confidence |
| `partial` | Some units/chunks usable |
| `blocked` | Cannot safely transform |
| `not_attempted` | Resolver/evaluator did not run |

For DITA, be stricter:

```text
DITA ready = article type known + DITA mapping exists + schema valid + no blocking diagnostics
```

For RAG, be more permissive:

```text
RAG ready = content segmented + text preserved + diagnostics included
```

But every RAG chunk should carry:

```text
article_type
article_confidence
unit_type
unit_confidence
triage_status
diagnostic_codes
source_path
source_span
```

That gives downstream retrieval the metadata it needs without lying to it. Very unfashionable, but useful.

---

## Phase 6: Build a seasoning corpus

You have one Azure Stack sample. Good start. Not enough.

You need a corpus that punishes the parser in several ways.

### Suggested corpus groups

| Corpus | Purpose |
|---|---|
| Microsoft Docs / Azure docs | Enterprise docs, metadata-heavy, mixed task/concept/reference |
| GitHub READMEs | Chaotic real-world Markdown, install/use/API sections |
| MkDocs / Material sites | Conventional docs structure |
| Docusaurus sites | Sidebar-oriented docs, front matter, admonitions |
| Pandoc-ish Markdown | Tables, footnotes, definitions, citations |
| Blog posts | Narrative Markdown, weak structure |
| API docs | Reference-heavy sections |
| Tutorials | Procedure-dominant content |
| Bad Markdown | Malformed headings, skipped levels, broken YAML, weird lists |
| Your own project docs | Dogfooding, because suffering should be circular |

The goal is not merely “parse all files.” It is to measure:

```text
parse success rate
schema validity rate
unknown article rate
unknown unit rate
false howto rate
reference resolution rate
diagnostics per 1,000 lines
RAG chunk quality
DITA transform confidence
round-trip/loss preservation
```

---

## Phase 7: Create a benchmark harness

You need a repeatable `season` command or test workflow.

Something like:

```bash
structure-parser season corpus/ \
  --out build/seasoning \
  --gold tests/gold/seasoning.yaml \
  --report build/seasoning/report.html
```

Outputs:

```text
inventory.csv
diagnostics.csv
classification_confusion.csv
schema_validation_summary.csv
readiness_summary.csv
unknown_units.csv
triage_evidence.jsonl
before_after_metrics.md
```

This gives you parser development as an empirical loop instead of vibes in a trench coat.

### Minimal scoring dashboard

| Metric | Early target |
|---|---:|
| Parse completion | 99%+ |
| Fatal parser errors | <1% |
| Unknown article rate | Acceptable if honest |
| Unknown unit rate | Decrease over time |
| False `howto` rate | Strong decrease |
| Schema-valid known articles | Increase over time |
| RAG chunk usability | 80%+ for structurally clean docs |
| DITA ready | Conservative, not inflated |

The key is that **unknown is not always bad**. False certainty is worse. Unknown means the parser knows where its semantic boundary is. That is maturity.

---

## Phase 8: Add golden tests, but not brittle fixture worship

Your implementation note is also right that the Azure outputs should become behavioral examples, not frozen fixtures.

Test the rule, not the incidental output.

Example tests:

```text
A document with Overview + Next steps must not classify as howto.
A document with Prerequisites + two ordered procedures + Next steps should classify as howto.
A table-heavy API Version section should classify as reference or fact.
A pre-H2 paragraph should classify as introduction.
A known procedure unit should validate against the procedure schema.
```

Also add mutation tests:

```text
Remove ordered list → howto confidence drops.
Add table-heavy reference section → howto dominance drops.
Change metadata from conceptual to howto → metadata conflict appears.
Rename Next steps → classification should not swing wildly.
```

That last one matters. A good classifier should not have a nervous breakdown because a heading changed from “Next steps” to “Where to go next.”

---

# Practical implementation sequence

Here is the order I would use.

## Milestone 1: Honesty layer

Add triage evidence objects and expose them in JSON/debug output.

Deliverables:

```text
ArticleTriageDecision model
UnitEvidence model
score/reason output
inspect-triage CLI command
triage evidence included in parsed JSON
```

Why first: every later improvement becomes easier to debug.

## Milestone 2: Conservative article scorer

Replace the current direct `_infer_article_type_from_units()` decision with scored candidates, margin rules, and dominance checks.

Deliverables:

```text
candidate scores
min_score
min_margin
dominance_ratio
topic fallback
ambiguous/degraded triage status
```

Why second: this directly addresses the false `howto` issue.

## Milestone 3: Unit classifier expansion

Add generic heading and construction evidence.

Deliverables:

```text
reference/fact heading patterns
concept/process/principle heading patterns
table-heavy detection
link-list detection
procedure dominance detection
pre-H2 introduction rule
```

Why third: article scoring improves only if unit evidence improves.

## Milestone 4: Schema/runtime alignment

Fix mismatches between emitted Pydantic model fields and JSON Schema expectations.

Pay special attention to:

```text
unitPrerequisites information_type
procedure_representation vs procedureRepresentation
schema aliases
known units failing validation
```

Why fourth: otherwise validation failures remain ambiguous.

## Milestone 5: Readiness reform

Split transform possibility from semantic compliance.

Deliverables:

```text
ready/degraded/partial/blocked statuses
blocking reasons
schema validity included in DITA readiness
confidence metadata included in RAG chunks
```

Why fifth: this makes downstream consumers trust the reports.

## Milestone 6: Seasoning corpus + benchmark harness

Create repeatable corpus evaluation.

Deliverables:

```text
corpus manifest
gold expectations
metrics reports
before/after comparison
classification confusion report
diagnostics trend report
```

Why sixth: now you can improve empirically.

---

# My blunt read

You are in a strong position.

The parser already has the right shape: layered architecture, Pydantic contracts, schema validation, CLI/API, diagnostics, pipeline mode, references, and readiness reports. That is more than most “semantic Markdown” ideas ever get before they dissolve into conference vapor. 

The current failures are not embarrassing. They are exactly the failures you want at this stage:

```text
The parser preserved structure.
The parser produced usable segmentation.
The parser exposed diagnostics.
The parser revealed that classification was too eager.
The parser revealed readiness/compliance ambiguity.
```

That is a productive failure profile.

The danger is adding ad hoc rules until the parser becomes a museum of whatever corpus hurt it last. Do not do that. Keep the parser generic. Add evidence types, scoring, confidence, and corpus-level regression. Make it conservative. Let it say `topic`, `ambiguous`, or `degraded` without shame.

The north star should be:

> Preserve everything. Classify only when evidence is strong. Explain every classification. Validate contracts separately. Report readiness honestly.

That is how this becomes not just a parser, but a **semantic contract engine for Markdown**. Which is, irritatingly enough, the useful version of the idea.