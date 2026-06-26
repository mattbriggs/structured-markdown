# Structured Markdown Semantic Layer: Project Framing, Documentation Notes, Use Cases, and Requirements

## 1. Executive Framing

Structured Markdown is an open semantic layer for Markdown. It parses constrained Markdown into a stable, validated object model with provenance, enabling reliable transformation into downstream systems such as RAG pipelines, JSON-LD, DITA, RSS/Atom, knowledge graphs, static sites, and structured documentation workflows.

The project should not be framed as a Markdown parser alone. The parser is a reference implementation. The real value is the semantic contract between human-authored Markdown and machine-readable content systems.

## 2. Core Positioning Statement

Structured Markdown turns Markdown into a validated semantic source format that can project into RAG, JSON-LD, DITA, RSS, graph data, and other machine-readable systems.

Alternative concise formulation:

Structured Markdown is a semantic compiler layer for Markdown: it normalizes human-readable Markdown into a validated object model, then projects that model into RAG chunks, JSON-LD, DITA, RSS, graph data, and publishing formats.

## 3. Strategic Category

Structured Markdown belongs in the category of semantic Markdown interoperability.

It should be understood as:

- A semantic contract layer.
- A Markdown semantic interoperability layer.
- A semantic intermediate representation for Markdown-based knowledge.
- A bridge between human-authored Markdown and machine-operated semantic workflows.
- A standards-oriented project, not merely an implementation.

## 4. What the Project Is

Structured Markdown is:

- A constrained Markdown authoring profile.
- A semantic object model.
- A canonical JSON serialization.
- A validation framework.
- A conformance test suite.
- A projection system for downstream formats.
- A reference implementation for parsing Markdown into structured semantic objects.
- A foundation for semantic content workflows, documentation automation, and AI-ready ingestion.

## 5. What the Project Is Not

Structured Markdown is not:

- A replacement for Markdown.
- A replacement for CommonMark.
- A universal ontology.
- A DITA-only conversion tool.
- A RAG-only ingestion tool.
- A proprietary enterprise content system.
- A general-purpose Markdown flavor without validation.
- An AI-only conversion engine.
- A parser whose behavior defines the standard.

The parser implements the standard. It does not constitute the standard by itself.

## 6. Primary Value Proposition

Markdown is widely used because it is readable, portable, and easy to author. However, ordinary Markdown lacks stable semantic contracts. It is often insufficient for structured documentation, knowledge graph ingestion, linked data publication, DITA transformation, RSS generation, and reliable RAG workflows.

Structured Markdown provides the missing intermediate layer:

```text
Human-readable Markdown
        ↓
Structured Markdown authoring profile
        ↓
Semantic object model / SMD-JSON
        ↓
Validation, provenance, diagnostics
        ↓
Target projections
```

## 7. Core Architecture

```text
                 ┌─────────────┐
                 │  Markdown   │
                 └──────┬──────┘
                        │
                        ▼
              ┌────────────────────┐
              │ Structured Markdown │
              │ Parser              │
              └────────┬───────────┘
                       │
                       ▼
              ┌────────────────────┐
              │ Semantic Object     │
              │ Model / SMD-JSON    │
              └────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   RAG chunks       JSON-LD          DITA
        ▼              ▼              ▼
   Retrieval       Linked data    CCMS / docs

        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      RSS            HTML          Graph
```

The semantic object model is the center of the architecture. All target outputs are projections from the same normalized semantic contract.

## 8. Key Design Principle: Intermediate Representation

Structured Markdown should be framed as a semantic intermediate representation.

The toolchain should not be:

```text
Markdown → RAG
Markdown → DITA
Markdown → RSS
Markdown → JSON-LD
```

Instead, it should be:

```text
Markdown → SMD Semantic Object Model → Projection
```

This avoids a collection of bespoke converters and establishes a stable, testable contract for all downstream outputs.

## 9. Layered Model

Structured Markdown should define three major layers.

### 9.1 Authoring Profile

The authoring profile defines the constrained Markdown patterns, metadata conventions, component syntax, and semantic markers that authors use.

Example:

```markdown
---
smd_profile: concept
id: semantic-layer
title: Semantic Layer
---

# Semantic Layer

A semantic layer defines stable meaning over source content.

## Definition

A semantic layer is a normalized representation between source content and downstream systems.
```

### 9.2 Semantic Object Model

The semantic object model defines the normalized, format-independent structure produced from the source.

Example:

```json
{
  "type": "Document",
  "profile": "concept",
  "id": "semantic-layer",
  "title": "Semantic Layer",
  "units": [
    {
      "type": "Definition",
      "title": "Definition",
      "content": [
        {
          "type": "Paragraph",
          "text": "A semantic layer is a normalized representation between source content and downstream systems."
        }
      ]
    }
  ],
  "provenance": {
    "source": "semantic-layer.md"
  }
}
```

### 9.3 Projections

A projection is a target-specific rendering or transformation of the semantic object model.

Examples:

- SMD-JSON to RAG chunks.
- SMD-JSON to JSON-LD.
- SMD-JSON to DITA.
- SMD-JSON to RSS/Atom.
- SMD-JSON to graph nodes and edges.
- SMD-JSON to HTML.
- SMD-JSON to validation reports.

## 10. Projection Types

| Projection | Purpose |
|---|---|
| RAG projection | Emits retrieval-ready chunks, metadata, citations, provenance, and source references. |
| JSON-LD projection | Emits linked-data-compatible entities and relationships. |
| DITA projection | Emits topic-like structures such as concept, task, reference, troubleshooting, or glossary topics. |
| RSS/Atom projection | Emits feed items from document units, updates, articles, or release notes. |
| Graph projection | Emits nodes and edges for knowledge graph ingestion. |
| HTML projection | Emits structured web content. |
| Audit projection | Emits validation, diagnostics, semantic completeness, and structure reports. |
| Static site projection | Emits pages, navigation metadata, and publishable site structures. |

## 11. Semantic Contract Definition

A Structured Markdown semantic contract defines:

1. Source syntax constraints.
2. Object model shape.
3. Required metadata.
4. Allowed semantic roles.
5. Provenance rules.
6. Validation rules.
7. Extension rules.
8. Transformation guarantees.
9. Diagnostic requirements.
10. Target projection expectations.

A document conforms to a Structured Markdown profile when its source can be parsed into the declared semantic object model and validated against the declared schema without required-rule violations.

## 12. Core Concepts

### Document

The root semantic object produced from a Markdown source file or source unit.

### Unit

A meaningful content division, usually derived from headings, explicit component markers, or profile-defined boundaries.

### Block

A structural content element such as paragraph, list, code block, admonition, definition, step, warning, note, table, or example.

### Inline

Inline semantic content such as emphasis, code span, reference, term, citation, link, or metadata-bearing phrase.

### Component

A typed semantic structure defined by a core profile or extension profile.

### Profile

A declared semantic rule set that constrains allowed structures and validates the document.

### Projection

A target-specific output derived from the semantic object model.

### Provenance

The trace between semantic objects and the source Markdown ranges that produced them.

### Diagnostic

A machine-readable warning, error, or informational message generated during parsing or validation.

## 13. Relationship to Markdown and CommonMark

Structured Markdown should not replace Markdown or CommonMark.

Recommended positioning:

Structured Markdown is not a replacement for CommonMark. It is a semantic authoring profile and object model layered above Markdown parsing.

CommonMark provides a useful precedent because it defines an unambiguous Markdown syntax and a test suite. Structured Markdown should similarly provide a specification, schemas, and conformance tests, but at the semantic layer rather than only at the syntax layer.

## 14. Relationship to JSON Schema

The canonical serialization should be SMD-JSON.

JSON Schema should be used to validate the object model and profile-specific structures.

The standard should distinguish between:

- The abstract semantic model.
- The canonical JSON serialization.
- The JSON Schema validation layer.
- Optional downstream projections such as JSON-LD, RDF, or DITA.

The JSON format should not be treated as the entire standard. It is the canonical serialization of the semantic model.

## 15. Relationship to JSON-LD and Linked Data

Structured Markdown should support optional JSON-LD output through a mapping layer.

Recommended positioning:

SMD-JSON is the canonical serialization. SMD-LD defines an optional JSON-LD context for linked-data interoperability.

Example JSON-LD context:

```json
{
  "@context": {
    "smd": "https://structuredmarkdown.org/ns#",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "title": "schema:name",
    "description": "schema:description",
    "concept": "skos:Concept",
    "broader": "skos:broader",
    "narrower": "skos:narrower"
  }
}
```

## 16. Relationship to DITA

DITA should be treated as a projection target, not as the governing model.

Recommended positioning:

DITA mappings are supported as a transformation target, not as the governing model.

Possible mappings:

| Structured Markdown Profile | DITA Target |
|---|---|
| concept | concept topic |
| task | task topic |
| reference | reference topic |
| troubleshooting | troubleshooting topic |
| glossary | glossentry |
| map/navigation | ditamap-like structure |
| reusable component | conref/keyref-compatible structure |

## 17. Relationship to RAG

RAG is a major use case but should not govern the core model.

Recommended positioning:

Structured Markdown supports RAG-ready semantic projection.

The RAG projection should add target-specific structures such as:

- Chunk boundaries.
- Chunk purpose.
- Retrieval metadata.
- Citation targets.
- Embedding-ready text.
- Source trace.
- Update and version metadata.
- Semantic labels.
- Relationship context.

The core semantic model should remain broader and should focus on:

- Document.
- Unit.
- Block.
- Inline.
- Reference.
- Metadata.
- Relationship.
- Provenance.
- Diagnostic.
- Profile.

## 18. Use Cases

### 18.1 RAG-Ready Content Ingestion

#### Problem

RAG pipelines often chunk Markdown using arbitrary size, heading heuristics, or HTML extraction. This leads to weak retrieval, missing context, poor citation, and inconsistent answers.

#### Structured Markdown Role

Structured Markdown provides semantic chunk boundaries, metadata, content type labels, and provenance.

#### Input

```markdown
---
smd_profile: concept
id: semantic-chunking
---

# Semantic Chunking

Semantic chunking divides content by meaning rather than arbitrary token length.

## Definition

A semantic chunk is a unit of content with a stable subject, purpose, and provenance.
```

#### Projection Output

```json
{
  "type": "RagChunk",
  "id": "semantic-chunking.definition",
  "title": "Definition",
  "text": "A semantic chunk is a unit of content with a stable subject, purpose, and provenance.",
  "semantic_role": "definition",
  "source": "semantic-chunking.md",
  "document_id": "semantic-chunking"
}
```

#### Value

- Better retrieval.
- Better citations.
- Better update tracking.
- Reduced arbitrary chunking.
- More predictable AI answers.

### 18.2 Markdown to JSON-LD

#### Problem

Markdown is human-readable but not inherently linked-data-compatible.

#### Structured Markdown Role

Structured Markdown creates typed entities and relationships that can be projected into JSON-LD.

#### Value

- Markdown becomes linked-data-compatible.
- Semantic relationships can be exposed.
- Content can participate in web-scale structured data workflows.

### 18.3 Markdown to DITA

#### Problem

DITA is semantically powerful but heavy for many authors. Markdown is lightweight but weakly structured.

#### Structured Markdown Role

Structured Markdown provides a lightweight authoring layer that can map to DITA-like topic structures.

#### Value

- Easier authoring.
- Structured output.
- Migration path into enterprise content systems.
- DITA-compatible semantic patterns without requiring authors to write XML.

### 18.4 Markdown to RSS/Atom

#### Problem

Markdown publishing workflows often require manual metadata and feed generation.

#### Structured Markdown Role

Structured Markdown can identify article/update/feed-item structures and project them into RSS or Atom.

#### Value

- Markdown becomes a structured publishing source.
- Feed generation becomes deterministic.
- Metadata is validated before publication.

### 18.5 Markdown to Knowledge Graph

#### Problem

Knowledge graphs require entities and relationships, but Markdown usually stores knowledge as flat text.

#### Structured Markdown Role

Structured Markdown identifies concepts, references, relationships, definitions, procedures, and dependencies.

#### Value

- Human-authored Markdown becomes graph-ingestible.
- Content relationships can be queried.
- Downstream systems can detect orphan concepts, unresolved references, and related topics.

### 18.6 Documentation Validation

#### Problem

Markdown documentation often lacks enforceable structure, required sections, semantic completeness, or profile-specific rules.

#### Structured Markdown Role

Structured Markdown profiles define required structures and validation rules.

#### Value

- Documentation quality can be tested.
- Missing sections can be detected.
- Semantic completeness can be measured.
- CI/CD workflows can reject invalid content.

### 18.7 Requirements and Specification Modeling

#### Problem

Requirements written in Markdown are readable but often ambiguous and difficult to validate or trace.

#### Structured Markdown Role

Structured Markdown can model requirements, assumptions, decisions, constraints, acceptance criteria, and traceability.

#### Value

- Requirements become machine-readable.
- Traceability can be generated.
- Implementation and testing can be connected to source requirements.

### 18.8 Static Site and Multi-Channel Publishing

#### Problem

Markdown is often used for static sites, but site generation commonly loses semantic intent.

#### Structured Markdown Role

Structured Markdown can project content into HTML while preserving semantic metadata and navigation structures.

#### Value

- Better site generation.
- Stronger metadata.
- Better search.
- Better content reuse.
- Compatibility with semantic web and AI retrieval workflows.

## 19. Standardization Strategy

Structured Markdown should first become a de facto standard before pursuing formal standardization.

Maturity ladder:

| Stage | Label | Meaning |
|---|---|---|
| 0 | Project | Parser exists. |
| 1 | Draft Spec | Model, rules, and schema documented. |
| 2 | Reference Implementation | Parser conforms to spec. |
| 3 | Testable Profile | Public conformance fixtures exist. |
| 4 | Multi-Implementation | At least two tools consume or produce it. |
| 5 | Community Draft | External users file issues and contribute cases. |
| 6 | De Facto Standard | Used in real workflows. |
| 7 | Formal Submission | Submitted to W3C, IETF, OASIS, or similar if useful. |

Current likely stage: Stage 0 moving into Stage 1.

## 20. Adoption Strategy

### 20.1 Initial Audience

Target people who already care about semantic structure:

- Semantic web practitioners.
- Knowledge graph builders.
- Documentation architects.
- DITA and content strategy professionals.
- AI/RAG builders.
- Developer documentation teams.
- Standards-minded information architects.
- Content governance teams.
- Static site and publishing pipeline maintainers.

### 20.2 Do Not Target Generic Markdown Users First

Generic Markdown users often value simplicity over structure. Structured Markdown should instead target workflows where semantic stability, validation, transformation, and machine-readability matter.

### 20.3 Adoption Hooks

Write short, shareable essays or docs such as:

- Markdown Is Not a Semantic Contract.
- Why RAG Needs Document Semantics Before Chunking.
- Structured Markdown as an Intermediate Representation.
- From Markdown to JSON-LD Without Losing the Author.
- DITA, Markdown, and the Missing Middle Layer.
- AI Conversion Needs Validation, Not Just Generation.
- Semantic Contracts for Human-Authored Content.
- Markdown as Source for Knowledge Graphs.

## 21. Public Repository Structure

Recommended repo structure:

```text
structured-markdown/
  README.md
  CHARTER.md
  SPECIFICATION.md
  GOVERNANCE.md
  ROADMAP.md
  LICENSE
  /spec
    00-overview.md
    01-terminology.md
    02-authoring-profile.md
    03-semantic-model.md
    04-json-serialization.md
    05-validation.md
    06-conformance.md
    07-extension-model.md
    08-mappings.md
  /schemas
    smd-document.schema.json
    smd-unit.schema.json
    smd-block.schema.json
    smd-inline.schema.json
    smd-reference.schema.json
    smd-diagnostic.schema.json
  /examples
    basic-document/
    concept-topic/
    task-topic/
    glossary-entry/
    troubleshooting/
    requirements/
    ai-rag-chunking/
    dita-bridge/
    json-ld-export/
    rss-feed/
    graph-export/
  /tests
    conformance/
  /mappings
    json-ld/
    rdf/
    dita/
    schema-org/
    skos/
    rss/
    rag/
    html/
    graph/
  /reference-implementation
    python/
  /docs
```

## 22. Required Documentation Files

### 22.1 CHARTER.md

Purpose:

Define the project, goals, non-goals, audience, governance, and adoption path.

Suggested sections:

- Purpose.
- Problem statement.
- Goals.
- Non-goals.
- Audience.
- Relationship to Markdown/CommonMark.
- Relationship to DITA.
- Relationship to JSON Schema.
- Relationship to JSON-LD.
- Conformance model.
- Governance.
- Versioning.
- Adoption path.

### 22.2 SPECIFICATION.md

Purpose:

Define the normative behavior of Structured Markdown.

Suggested sections:

- Scope.
- Terminology.
- Source document model.
- Semantic object model.
- Parsing rules.
- Validation rules.
- Extension mechanism.
- Profiles.
- Diagnostics.
- Provenance.
- Conformance.

### 22.3 SEMANTIC-MODEL.md

Purpose:

Define the abstract object model independent of JSON.

Suggested sections:

- Document.
- Unit.
- Block.
- Inline.
- Metadata.
- Reference.
- Relationship.
- Provenance.
- Diagnostic.
- Profile.
- Extension.

### 22.4 JSON-SERIALIZATION.md

Purpose:

Define the canonical SMD-JSON representation.

Suggested sections:

- Root object.
- Object typing.
- Required fields.
- Optional fields.
- IDs.
- References.
- Source ranges.
- Metadata model.
- Profile declarations.
- Versioning.

### 22.5 CONFORMANCE.md

Purpose:

Define how documents, parsers, validators, transformers, and projections conform.

Suggested sections:

- Document conformance.
- Parser conformance.
- Validator conformance.
- Projection conformance.
- Test suite requirements.
- Error and warning requirements.
- Version compatibility.

### 22.6 USE-CASES.md

Purpose:

Show practical uses and adoption surfaces.

Suggested structure for each use case:

- Problem.
- Structured Markdown role.
- Input example.
- SMD-JSON output.
- Projection output.
- Value.
- Requirements.

## 23. Normative Language

Use RFC-style normative language:

- MUST.
- MUST NOT.
- SHOULD.
- SHOULD NOT.
- MAY.

Example rules:

```text
SMD-DOC-001: A Structured Markdown document MUST produce a root Document object.

SMD-UNIT-002: A heading of level 2 or lower SHOULD produce a Unit object unless the active profile defines an alternate grouping rule.

SMD-PROV-001: Every emitted semantic object MUST include provenance linking it to the source range that produced it.

SMD-EXT-001: Extensions MUST declare a namespace, version, schema URI, and fallback behavior.
```

## 24. Conformance Levels

Structured Markdown should support progressive adoption.

| Level | Name | Description |
|---|---|---|
| 0 | Compatible Markdown | Document remains readable as normal Markdown. |
| 1 | Structured Document | Document uses heading, metadata, and block conventions that produce stable units. |
| 2 | Semantic Components | Document uses typed semantic blocks/components. |
| 3 | Validated Semantic Contract | Document validates against a declared schema/profile. |
| 4 | Transformable | Document can project into target formats without semantic loss inside the declared scope. |

## 25. Profiles

Profiles define allowed structures and validation rules for specific domains.

Potential profiles:

- smd-core.
- smd-docs.
- smd-rag.
- smd-dita.
- smd-json-ld.
- smd-skos.
- smd-requirements.
- smd-learning.
- smd-troubleshooting.
- smd-api-reference.
- smd-decision-record.
- smd-rss.

Example profile declaration:

```yaml
id: smd-troubleshooting
version: 0.1
extends: smd-core
allowed_units:
  - problem
  - cause
  - solution
  - verification
required_fields:
  - title
  - problem
validation:
  - rule: troubleshooting.solution.required
```

## 26. Extension Model

Extensions should be strict and declared.

Each extension should require:

1. Namespace.
2. Version.
3. Schema URI.
4. Component name.
5. Allowed child structures.
6. Required fields.
7. Fallback behavior.
8. Optional projection rules.
9. Optional rendering hints.

Example:

```json
{
  "namespace": "smd-task",
  "version": "0.1",
  "component": "procedure",
  "schema": "https://example.org/schemas/procedure.schema.json",
  "fallback": "section"
}
```

Arbitrary custom blocks without declared semantics should not be considered conforming.

## 27. Core Functional Requirements

### Parser Requirements

- The parser MUST accept Markdown source.
- The parser MUST produce a root Document object.
- The parser MUST preserve source provenance for emitted objects.
- The parser MUST emit diagnostics for invalid or ambiguous structures.
- The parser SHOULD support declared profiles.
- The parser SHOULD support extension namespaces.
- The parser MUST produce deterministic output for the same input and profile.

### Object Model Requirements

- The object model MUST represent documents, units, blocks, inlines, metadata, references, relationships, provenance, and diagnostics.
- The object model MUST be serializable as canonical JSON.
- The object model SHOULD be independent of any single downstream format.
- The object model MUST support profile declarations.
- The object model MUST support versioning.

### Validation Requirements

- The validator MUST validate SMD-JSON against JSON Schema.
- The validator SHOULD validate profile-specific rules.
- The validator MUST distinguish errors, warnings, and informational diagnostics.
- The validator SHOULD produce machine-readable validation reports.
- The validator SHOULD support CI/CD use.

### Projection Requirements

- Projections MUST consume validated SMD-JSON.
- Projections SHOULD declare supported profiles.
- Projections MUST preserve provenance where the target format supports it.
- Projections SHOULD emit diagnostics when semantic loss occurs.
- Projections SHOULD be testable with fixtures.

### RAG Projection Requirements

- The RAG projection MUST emit retrieval-ready chunks.
- Each chunk MUST include source provenance.
- Each chunk SHOULD include semantic role.
- Each chunk SHOULD include document ID, unit ID, title, and hierarchy context.
- Each chunk SHOULD include citation metadata.
- The projection SHOULD preserve relationships between chunks.

### JSON-LD Projection Requirements

- The JSON-LD projection SHOULD provide a JSON-LD context.
- It SHOULD map document metadata to known vocabularies where appropriate.
- It MAY support schema.org, SKOS, Dublin Core, or other vocabularies through mappings.
- It MUST NOT require the core model to be RDF-native.

### DITA Projection Requirements

- The DITA projection SHOULD map supported profiles to DITA-compatible topic structures.
- It SHOULD emit diagnostics when a structure cannot be mapped cleanly.
- It SHOULD preserve topic IDs, titles, hierarchy, and semantic roles.
- It SHOULD not force the core model to be DITA-specific.

### RSS/Atom Projection Requirements

- The RSS/Atom projection SHOULD identify feed items from documents or units.
- It MUST require title, link or ID, date, and content summary where needed.
- It SHOULD validate required feed metadata.
- It SHOULD preserve source references.

## 28. Nonfunctional Requirements

### Stability

- Output should be deterministic.
- The semantic model should be versioned.
- Breaking changes should require major version changes.

### Interoperability

- The core model should not depend on one downstream format.
- Projections should be optional.
- Profiles should be modular.

### Readability

- Source Markdown should remain readable as Markdown.
- Semantic annotations should be minimally intrusive.

### Testability

- All normative parsing rules should have fixtures.
- Conformance tests should compare input Markdown, expected SMD-JSON, and expected diagnostics.

### Extensibility

- Extensions should use namespaces.
- Extensions should declare schemas.
- Extensions should declare fallback behavior.

### Provenance

- Semantic objects should be traceable to source ranges.
- Projections should preserve provenance where possible.

### AI Compatibility

- The model should support retrieval, citation, chunking, and content governance.
- AI output should be validated before being treated as conforming Structured Markdown.

## 29. Conformance Test Suite

Each fixture should include:

```text
tests/
  headings/
    heading-basic.md
    heading-basic.expected.json
    heading-basic.diagnostics.json
  lists/
  references/
  admonitions/
  invalid/
```

Each test should define:

1. Input Markdown.
2. Expected SMD-JSON.
3. Expected diagnostics.
4. Valid, invalid, or warning-only status.
5. Applicable specification rule IDs.

Example:

```json
{
  "rule": "SMD-BLOCK-003",
  "description": "A second-level heading begins a new unit unless explicitly nested.",
  "input": "## Install\nText.",
  "expected": {
    "type": "Unit",
    "title": "Install"
  }
}
```

## 30. Initial Release Scope

Recommended v0.1 release:

- Charter.
- Core specification.
- Semantic model.
- JSON serialization.
- JSON Schema package.
- Reference parser.
- CLI validator.
- 10 to 20 examples.
- Conformance fixtures.
- RAG projection demo.
- JSON-LD projection demo.
- DITA projection demo.
- RSS projection demo.
- Documentation site.

## 31. CLI Commands

Potential CLI interface:

```bash
smd parse input.md --out document.smd.json
smd validate input.md
smd validate-json document.smd.json
smd test-conformance
smd project input.md --to rag
smd project input.md --to json-ld
smd project input.md --to dita
smd project input.md --to rss
smd project input.md --to html
```

Alternative verb:

```bash
smd transform input.md --to dita
```

Use `project` if the architecture emphasizes projections from the semantic model.

## 32. Public-Facing README Draft

```markdown
# Structured Markdown Semantic Model

Structured Markdown is an experimental semantic layer for Markdown. It parses constrained Markdown into a validated semantic object model with provenance, enabling reliable projection into RAG chunks, JSON-LD, DITA, RSS/Atom, graph data, HTML, and other machine-readable formats.

The project provides:

- a draft specification
- a constrained Markdown authoring profile
- a semantic object model
- canonical SMD-JSON serialization
- JSON Schema validation
- conformance fixtures
- projection examples
- a reference parser

Structured Markdown is not a replacement for Markdown or CommonMark. It is a semantic interoperability layer for workflows that need stable structure, validation, transformation, and machine-readable content.
```

## 33. White Paper Concept

Suggested title:

Semantic Contracts for Markdown: A Structured Intermediate Model for Content, Knowledge Graphs, and AI Retrieval

Suggested sections:

1. Abstract.
2. Problem: Markdown is readable but semantically unstable.
3. Why syntax is not enough.
4. The need for semantic contracts.
5. Structured Markdown overview.
6. Authoring profile.
7. Semantic object model.
8. Validation and conformance.
9. Projection architecture.
10. RAG-ready semantic ingestion.
11. JSON-LD and linked data.
12. DITA transformation.
13. RSS and publishing pipelines.
14. Knowledge graph ingestion.
15. Governance and extensibility.
16. Adoption path.
17. Conclusion.

## 34. Career and Ecosystem Positioning

The project has career value if it becomes evidence of:

- Semantic architecture judgment.
- Interoperability design.
- Standards-oriented thinking.
- Open-source leadership.
- Content systems engineering.
- AI-ready knowledge infrastructure.
- Practical bridge-building between documentation, linked data, and RAG.

Professional framing:

Matt Briggs defined a practical semantic contract layer for Markdown-based knowledge systems.

Better career category:

- Semantic content systems architect.
- AI content infrastructure strategist.
- Documentation platform architect.
- Knowledge architecture lead.
- Content intelligence consultant.

## 35. Public Adoption Strategy

### Step 1: Publish Coherent v0.1

Do not wait for perfection. Publish enough for others to understand the architecture.

### Step 2: Build Examples

Examples are the adoption engine. Each example should show:

```text
Markdown source
→ SMD-JSON
→ validation report
→ projection output
```

### Step 3: Write Explainers

Publish short articles that create conceptual doorways.

### Step 4: Invite Profile Contributions

Avoid letting people rewrite the core model early. Invite profile and projection contributions first.

### Step 5: Seek Independent Implementations

A standard-like project becomes more credible when at least two tools can produce or consume the model.

Potential second implementations:

- TypeScript validator.
- VS Code extension.
- GitHub Action.
- Pandoc filter.
- Static site plugin.
- DITA transformer.

### Step 6: Consider Standards Incubation

Only after community use exists, consider:

- W3C Community Group.
- IETF Internet-Draft.
- OASIS technical committee.
- Other semantic web or documentation standards venues.

## 36. Messaging Guardrails

Do not lead with:

- “I created a new Markdown standard.”
- “This replaces Markdown.”
- “This is for Heretto.”
- “This is a RAG tool.”
- “This is a DITA converter.”

Lead with:

- “This is a semantic layer for Markdown.”
- “This creates a stable intermediate representation.”
- “This makes Markdown machine-readable without abandoning human readability.”
- “This supports RAG, JSON-LD, DITA, RSS, and graph projections.”
- “This is a semantic contract for Markdown-based content systems.”

## 37. Strongest One-Sentence Pitch

Structured Markdown is an open semantic contract for turning Markdown into validated, transformable, machine-readable content.

## 38. Strongest Technical Pitch

Structured Markdown is a semantic compiler layer for Markdown: it normalizes human-readable Markdown into a validated object model, then projects that model into RAG chunks, JSON-LD, DITA, RSS, graph data, and publishing formats.

## 39. Immediate Next Actions

1. Create `CHARTER.md`.
2. Create `SPECIFICATION.md`.
3. Define the core semantic object model.
4. Define SMD-JSON.
5. Create JSON Schema files.
6. Create 10 representative examples.
7. Create conformance fixtures.
8. Build a minimal parser-to-SMD-JSON path.
9. Build at least two projections: RAG and JSON-LD.
10. Add DITA and RSS projections as proof of generality.
11. Publish a white paper.
12. Write short public explainers.
13. Invite feedback from semantic content, knowledge graph, RAG, and documentation architecture communities.

## 40. Final Framing

The project is not merely a useful parser. It is a semantic normalization layer for Markdown.

Its value is the stable middle:

```text
Markdown → Semantic Contract → Many Targets
```

That middle layer is what makes the project standard-like, extensible, and broadly useful.
