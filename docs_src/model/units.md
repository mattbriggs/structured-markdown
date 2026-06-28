# Unit Types

A unit is the logical section of an article. Each unit begins at an H2 heading and ends where the next H2 heading begins (or at the end of the document). The unit contains an ordered array of components — the block-level elements that follow its heading. A unit's `unitType` field encodes its rhetorical function: what the section is for. Its `informationType` field encodes its Horn classification: the kind of knowledge the section conveys. Together, these two fields give downstream tools a typed, machine-readable signal about the purpose of every section in a document.

The Information Mapping design vocabulary includes seven Horn information types. The full design set is `concept`, `procedure`, `process`, `principle`, `fact`, `structure`, and `classification`; the current runtime enum implements `concept`, `procedure`, `process`, `principle`, and `fact`, plus `mixed` and `unknown` parser states.

## Unit Type Inference

The parser infers unit type from the text of the H2 heading using keyword matching. The heading is normalized to lowercase and matched against a keyword table. When a heading matches multiple keywords, the most specific match wins; when no heading matches, the parser inspects construction evidence such as ordered lists or code-only sections before falling back to `unitUnknown`. The inference is deterministic and author-controllable through heading conventions; future `unitType` annotations would add an explicit unit-level override without changing heading text.

## Unit Type Reference

| Unit Type | Information Type | Heading Keywords (Inferred) | Purpose |
|---|---|---|---|
| introduction | (varies) | Introduction, Overview, About | Introduces the article |
| concept | concept | Concept, Background, What is | Explains an idea or thing |
| procedure | procedure | Steps, How to, Procedure | Ordered task steps |
| principle | principle | Principles, Guidelines, Rules | Policies or design constraints |
| process | process | How it works, Process, Mechanism | Describes a workflow or mechanism |
| fact | fact | Facts, Parameters, Values | Lookup-oriented data |
| reference | fact | Reference, Options, Parameters, Configuration | Reference table or list |
| troubleshooting | process | Troubleshooting, Symptoms, Issues | Symptom/condition/remedy |
| prerequisites | (varies) | Prerequisites, Before you begin, Requirements | Pre-conditions for a procedure |
| glossary | fact | Glossary | Contains glossentry units |
| glossentry | fact | (term headings) | One term and definition |
| link-nextstep | (varies) | Next Steps, What's next | Navigation to follow-on content |
| link-related | (varies) | Related, See also | Navigation to related content |
| unknown | unknown | (any unmatched heading) | Fallback |

The `structure` and `classification` information types are reserved for future model expansion. A structure unit would describe parts and relationships, while a classification unit would describe groups, classes, or taxonomies.

## Individual Unit Types

### unitIntroduction

The introduction unit orients the reader to the article. It typically appears first in the `content` array and contains a brief explanation of what the document covers, who it is for, and what the reader will be able to do after reading it. Expected components include one or more `compParagraph` blocks. It may also include a `compAlert` to call out scope limitations or prerequisites. The introduction unit does not carry a fixed `informationType` because its content is subordinate to the article type — an introduction to a concept article is conceptual; an introduction to a howto article is procedural in orientation.

### unitConcept

The concept unit explains a single idea, technology, or thing. Its `informationType` is `concept`. Expected components include paragraphs, optionally supplemented by lists, tables, or code blocks that illustrate the concept. A concept unit answers "What is X?" or "Why does X exist?" — it does not instruct the reader to perform a task. Articles of type `artConcept` and `artOverview` require at least one concept unit.

### unitProcedure

The procedure unit documents ordered task steps. Its `informationType` is `procedure`. The procedure unit type has three representation variants that differ in how the steps are rendered:

- **`unitProcedureOrderedlist`** — steps are expressed as a `compListOrdered` component. Use this variant when the steps are discrete, numbered actions that the reader follows in sequence.
- **`unitProcedureCodeblock`** — steps are expressed as a `compBlockCode` component. Use this variant when the procedure is a command sequence that the reader runs verbatim, such as a shell script or a series of CLI commands.
- **`unitProcedure`** — the mixed or general form, which may contain any combination of ordered lists, code blocks, paragraphs, and alerts. Use this variant when the procedure includes explanatory prose between steps or when steps and commands are interleaved.

Articles of type `artHowto`, `artQuickstart`, and `artTutorial` require at least one procedure unit in any of these three variants.

### unitPrinciple

The principle unit states a rule, policy, or design constraint. Its `informationType` is `principle`. Expected components include paragraphs and unordered lists. A principle unit answers "What rule governs X?" or "What constraint applies to X?" — it describes normative guidance rather than explaining what something is or instructing how to do it. Use `unitPrinciple` for design guidelines, governance policies, and architectural constraints.

### unitProcess

The process unit describes how something works — a mechanism, workflow, or algorithm. Its `informationType` is `process`. Expected components include paragraphs, optionally supplemented by ordered lists, tables, or diagrams embedded as code blocks (Mermaid). A process unit answers "How does X work?" — it describes causation, sequence, or transformation. It differs from `unitProcedure` in that the reader observes the process rather than performs it.

### unitFact

The fact unit presents lookup-oriented data: values, parameters, limits, or enumerated constants. Its `informationType` is `fact`. Expected components include tables, lists, and definition-style paragraphs. Use `unitFact` when the content is a set of discrete factual claims that readers will consult rather than read linearly. It differs from `unitReference` in that reference units are typically organized as a structured table or list with explicit column semantics, while fact units may use mixed presentation.

### unitReference

The reference unit presents a structured reference table or reference list. Its `informationType` is `fact`. Expected components are primarily `compTable` and `compListOrdered` or `compListUnordered`. A reference unit is the primary required unit for `artReference` articles. Its content is optimized for scanning: rows and columns with clear headers, or list items with consistent structure. Use `unitReference` when readers need to look up a specific value, option, or API parameter quickly.

### unitTroubleshooting

The troubleshooting unit documents one or more symptom/condition/remedy triples. Its `informationType` is `process`. The expected structure is: a description of the observable symptom, a diagnosis of the probable condition, and one or more remedies. Expected components include paragraphs, alerts (especially `compAlertWarning` or `compAlertCaution`), and ordered lists for multi-step remedies. Articles of type `artTroubleshooting` require at least one troubleshooting unit.

### unitPrerequisites

The prerequisites unit lists conditions, software, or knowledge the reader must have before beginning a procedure. Its `informationType` varies with the article type. Expected components include unordered lists and paragraphs. A prerequisites unit typically appears before the first procedure unit in a howto or tutorial article. Use `unitPrerequisites` rather than embedding prerequisites in the introduction when the list is long enough to warrant its own section.

### unitGlossary

The glossary unit is a container for `unitGlossentry` units. Its `informationType` is `fact`. It does not directly contain components in the way other units do; instead, its `content` array holds glossentry units. Use `unitGlossary` inside `artGlossary` articles to group related terms.

### unitGlossentry

The glossentry unit defines exactly one term. Its `informationType` is `fact`. It carries a `term` field (the term being defined) in addition to the standard unit fields. Expected components include one or more paragraphs that constitute the definition, optionally followed by examples or cross-references. Use `unitGlossentry` either inside a `unitGlossary` container or as the sole unit of an `artGlossentry` article.

### unitLinkNextstep

The link-nextstep unit provides navigation links to follow-on content — the logical next documents the reader should consult after completing the current article. Its `informationType` varies. Expected components include an unordered list of `compLink` items. Place a link-nextstep unit at the end of the article's `content` array.

### unitLinkRelated

The link-related unit provides navigation links to related content that is relevant but not necessarily the next step. Its `informationType` varies. Expected components include an unordered list of `compLink` items. Like link-nextstep, it typically appears at the end of the article. Use `unitLinkRelated` for cross-references to reference material, related concepts, or parallel procedures.

### unitUnknown

The unknown unit is the fallback for any section whose heading does not match a known keyword pattern. Its `informationType` is `unknown`. The parser assigns `unitUnknown` when classification heuristics produce no confident match. Content inside an unknown unit is preserved in full. Downstream tools can identify unknown units by their `unitType` field and route them for human review or reclassification.
