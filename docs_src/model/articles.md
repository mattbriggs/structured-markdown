# Article Types

An article schema defines the top-level contract for one Markdown file or one HTML page. It specifies which article type the content represents, which unit types must appear in the `content` array, which unit types are permitted but not required, and which shared base fields every article carries. All article schemas extend `sharedArticle.schema.json`, which provides the common fields — `schema`, `version`, `articleId`, `articleType`, `ditaType`, `informationType`, `title`, `triageStatus`, `metadata`, `source`, and `content`. Concrete article schemas layer additional constraints on top: required unit types, minimum item counts, and type-specific field defaults. The root union schema `artArticle.schema.json` is a `oneOf` that references all concrete schemas, so any compliant article can be validated against a single entry point.

## Quick Reference

| Schema | ditaType | informationType | Required Unit | Min Items |
|---|---|---|---|---|
| artTopic | topic | mixed | any | 1 |
| artConcept | concept | concept | unitConcept | 1 |
| artHowto | howto | procedure | unitProcedure (any) | 2 |
| artReference | reference | fact | unitReference | 1 |
| artTroubleshooting | troubleshooting | process | unitTroubleshooting | 1 |
| artGlossary | glossary | fact | unitGlossentry | 1 |
| artGlossentry | glossentry | fact | unitGlossentry | 1 |
| artOverview | concept | concept | unitConcept | 1 |
| artQuickstart | howto | procedure | unitProcedure (any) | 2 |
| artTutorial | howto | procedure | unitProcedure (any) | 2 |
| artUnknown | (none) | unknown | none | 0 |

## Sample Front Matter

The following front matter block illustrates the explicit declaration for a howto article. The parser reads these fields first to select the article schema; when they are absent or unsupported, it falls back to the constructed unit population and can still infer a howto article from procedure-oriented sections.

```yaml
---
articleType: howto
title: How to Configure the Parser
description: Configure structure-parser for strict validation in CI.
---
```

## Article Type Reference

### artTopic

The topic article type is the generic container for any content that fits a known unit type but does not specialize into a narrower article form. Its `ditaType` is `topic` and its `informationType` is `mixed`, reflecting that it imposes no single rhetorical purpose on the whole. Any combination of known unit types is valid in a topic article's `content` array, and the minimum item count is one. Use `artTopic` when the content is clearly structured and uses recognized unit types, but does not commit to a single information purpose — for example, a landing page that combines an introduction, a concept explanation, and a set of links.

### artConcept

The concept article type explains a single idea, technology, or thing. Its `ditaType` is `concept` and its `informationType` is `concept`. The `content` array must contain at least one `unitConcept` unit. Additional units of other types (introduction, principle, link-related) are permitted. Use `artConcept` when the primary goal of the document is to answer "What is X?" or "Why does X exist?" — not to instruct the reader to perform a task.

### artHowto

The howto article type documents a task-oriented procedure. Its `ditaType` is `howto` and its `informationType` is `procedure`. The `content` array must contain at least two items and must include at least one `unitProcedure` unit in any of its three representation variants (`unitProcedure`, `unitProcedureOrderedlist`, or `unitProcedureCodeblock`). The minimum of two items reflects the expectation that a procedural article carries at minimum an introduction or prerequisites unit alongside the procedure itself. Use `artHowto` when the primary goal is to instruct the reader to accomplish a specific, bounded task.

### artReference

The reference article type presents lookup-oriented facts, parameters, configuration options, or API specifications. Its `ditaType` is `reference` and its `informationType` is `fact`. The `content` array must contain at least one `unitReference` unit. Use `artReference` when readers will scan rather than read linearly — when the document's value is in the precision and completeness of its factual claims, not in narrative explanation or procedural instruction.

### artTroubleshooting

The troubleshooting article type documents symptoms, probable causes, and remedies. Its `ditaType` is `troubleshooting` and its `informationType` is `process`. The `content` array must contain at least one `unitTroubleshooting` unit. Use `artTroubleshooting` when the document's primary structure is the diagnostic loop: a reader arrives with an observed symptom, the article helps them identify the condition, and it prescribes a fix or workaround.

### artGlossary

The glossary article type is a collection of defined terms. Its `ditaType` is `glossary` and its `informationType` is `fact`. The `content` array must contain at least one `unitGlossentry` unit. A glossary article acts as the container for multiple term definitions, which appear as glossentry units (not individual glossentry articles). Use `artGlossary` when the document's sole purpose is to define terms — for example, a product glossary page or an API terminology reference.

### artGlossentry

The glossentry article type defines exactly one term. Its `ditaType` is `glossentry` and its `informationType` is `fact`. The `content` array must contain exactly one `unitGlossentry` unit. Use `artGlossentry` when a single term warrants its own standalone document — for example, when a term is complex enough to require extended explanation, examples, or cross-references that would be unwieldy inside a glossary collection.

### artOverview

The overview article type is a specialization of concept, designed for introductory documents that orient readers to a product, feature set, or system. Like `artConcept`, its `ditaType` is `concept` and its `informationType` is `concept`, and it requires at least one `unitConcept` unit. The distinction from `artConcept` is semantic and organizational: overview articles are typically the entry point to a documentation set, while concept articles explain a specific idea within that set. Use `artOverview` for "What is this product?" and "How does this system work at a high level?" documents.

### artQuickstart

The quickstart article type is a specialization of howto that prioritizes speed to value. Its `ditaType` is `howto` and its `informationType` is `procedure`. Like `artHowto`, it requires at least two items in `content` and at least one `unitProcedure` unit in any representation variant. The quickstart specialization signals to documentation systems and readers that the procedure is intentionally abbreviated — it covers the minimum steps to achieve a working result, not the full range of options. Use `artQuickstart` for "Get started in five minutes" and "Minimal working example" documents.

### artTutorial

The tutorial article type is a specialization of howto that prioritizes learning through guided practice. Its `ditaType` is `howto` and its `informationType` is `procedure`. Like `artHowto`, it requires at least two items in `content` and at least one `unitProcedure` unit. The tutorial specialization signals that the procedure is designed to teach — it may include explanation, context, and deliberate repetition that a pure task article would omit. Use `artTutorial` for documents where the reader's goal is to build understanding through doing, not merely to complete a task.

### artUnknown

The unknown article type is the fallback for content that cannot be classified into any concrete article type. It carries no `ditaType` value, its `informationType` is `unknown`, and it imposes no required units and no minimum item count on `content`. The parser assigns `artUnknown` when classification heuristics produce no confident match and the `triageStatus` field is set to `unknown` or `ambiguous`. Content in an unknown article is preserved in full — no information is discarded — and the article's `triageStatus` field signals to downstream tools that human review is needed.
