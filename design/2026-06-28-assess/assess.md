# Assessment of Parsed Azure Stack Documents

## Scope

This assessment reviews the six parsed JSON files in `design/2026-06-28-assess/`. The files are parser outputs, not source Markdown files, so the conclusions below assess the produced `ParsedDocument` objects: extracted metadata, article classification, unit segmentation, diagnostics, validation results, transform-readiness flags, references, and practical suitability for XML, DITA XML, and metadata-rich RAG chunking.

## Executive Summary

The parser successfully produced structured content for all six files. Every file has a title, source metadata, structured units, references, diagnostics, validation output, and transform-readiness records, so the parser did not fail at the basic parsing and normalization task.

The parser output is useful for generic XML and RAG ingestion but not yet cleanly compliant with the project schema standards. All six files are marked `dita:ready`, `schema_org:ready`, and `rag_ingestion:ready`, but all six also have `validation.valid: false` against `artHowto.schema.json`. This means the current readiness evaluator is checking minimum transformation prerequisites, while the schema validator is correctly reporting that the produced article/unit model does not yet satisfy the stricter authoring contract.

The largest quality issue is article-type overclassification as `howto`. All six files were classified as `howto`, even though the source metadata says several are `conceptual`, `overview`, or `article`. This appears to come from construction signals such as action-oriented headings and `Next steps` sections, which are currently enough to pull broad conceptual Microsoft Docs pages into the how-to schema.

The strongest output is `azure-stack-connect-vpn.md.json`. It has the best unit recognition rate, the clearest procedure structure, and the most useful RAG chunks. The weakest outputs are `azure-stack-arm-templates.md.json`, `azure-stack-compute-overview.md.json`, and `azure-stack-acs-differences.md.json`, where most H2 sections remain `unitUnknown` and the selected `howto` article type does not match the document's likely rhetorical purpose.

## Assessment Criteria

The XML readiness score measures whether the parsed object preserves enough structure to serialize to a generic XML representation. A high score means the parser captured title, metadata, units, components, nested list/table structures, inline attributes, and provenance well enough for loss-aware XML output.

The DITA XML readiness score measures whether the parsed object can be transformed into semantically appropriate DITA. A high score requires not only the project readiness flag, but also a plausible DITA topic type, known units, and schema-valid content.

The RAG chunk readiness score measures whether the parsed object can produce segmented, metadata-rich retrieval chunks. A high score means H2 unit boundaries are meaningful, unit types are mostly known, component text is preserved, metadata is available, and diagnostics are low enough that chunk labels can be trusted.

The compliance score measures conformance to the current Structured Markdown model and JSON Schema layer. A high score requires `validation.valid: true`, low unknown-unit counts, and an article type that agrees with the document's apparent source metadata and structure.

Scores use a 1-5 scale: 5 means ready, 4 means usable with minor cleanup, 3 means usable with caveats, 2 means degraded and requires remediation, and 1 means not ready.

## Evidence Summary

| File | Source topic | Parser article type | Units | Unknown units | Diagnostics | Validation | Readiness flags |
|---|---:|---:|---:|---:|---:|---:|---|
| `azure-stack-acs-differences.md.json` | `conceptual` | `howto` | 4 | 3 | 8 | false | DITA ready; Schema.org ready; RAG ready |
| `azure-stack-arm-templates.md.json` | `article` | `howto` | 9 | 8 | 13 | false | DITA ready; Schema.org ready; RAG ready |
| `azure-stack-compute-overview.md.json` | `conceptual` | `howto` | 5 | 4 | 9 | false | DITA ready; Schema.org ready; RAG ready |
| `azure-stack-connect-azure-stack.md.json` | `conceptual` | `howto` | 4 | 2 | 7 | false | DITA ready; Schema.org ready; RAG ready |
| `azure-stack-connect-vpn.md.json` | `conceptual` | `howto` | 8 | 1 | 6 | false | DITA ready; Schema.org ready; RAG ready |
| `azure-stack-considerations.md.json` | `overview` | `howto` | 6 | 3 | 8 | false | DITA ready; Schema.org ready; RAG ready |

## Per-File Assessment

### `azure-stack-acs-differences.md.json`

This document is structurally preserved but weakly classified. The source topic is `conceptual`, while the parser selected `howto` with `information_type: procedure`. Three of four units are unknown: the unnamed introductory material, `Cheat sheet: Storage differences`, and `API version`. Only `Next steps` was classified as procedure, which likely drove the how-to article type even though the document reads more like a reference/concept comparison.

This document is moderately ready for generic XML. The parser retained paragraphs, a table, lists, title, metadata, and references, so a neutral XML representation could preserve the content.

This document is not ready for high-quality DITA XML without remediation. The current readiness flag says `dita:ready`, but the selected how-to type is semantically suspect and `validation.valid` is false.

This document is usable but degraded for RAG chunking. The H2 boundaries are useful, but three chunks would be labeled `unknown`, reducing metadata quality and retrieval filtering value.

Scores: XML 4/5; DITA XML 2/5; RAG chunks 3/5; schema compliance 2/5.

### `azure-stack-arm-templates.md.json`

This document is parsed but poorly classified against the current model. The source topic is `article`, while the parser selected `howto`. Eight of nine units are unknown, and many headings are resource-template names rather than Horn/DITA section types. The only known unit is `Next steps`, classified as procedure.

This document is reasonably ready for generic XML. The parser retained the heading boundaries, paragraphs, and unordered lists, so a structure-preserving XML output is feasible.

This document is not ready for DITA XML as produced. The output validates against neither the selected how-to schema nor a clear alternate schema, because the article is mostly a curated index of template links and examples.

This document is weak for metadata-rich RAG chunks. The chunks are separable, but their labels are mostly `unknown`, so the output is closer to segmented Markdown than semantically enriched retrieval data.

Scores: XML 4/5; DITA XML 1/5; RAG chunks 2/5; schema compliance 1/5.

### `azure-stack-compute-overview.md.json`

This document is preserved but misclassified. The source topic is `conceptual`, while the parser selected `howto`. Four of five units are unknown, including `Before creating a VM`, `Create your first VM`, and `Manage your VM`; these sections contain tables, H3 headings, and mixed explanatory/list content that the classifier does not yet map cleanly.

This document is ready for generic XML with caveats. The parser captured paragraphs, lists, tables, and H3 headings, so the content can be represented in XML, but semantic tags would be generic for most units.

This document is not ready for reliable DITA XML. A DITA concept or topic mapping would likely fit better than `howto`, and the schema validation failure confirms that the current classified model is not compliant.

This document is usable but degraded for RAG. The section boundaries are meaningful, but the unknown unit labels would limit downstream chunk filtering by information type.

Scores: XML 4/5; DITA XML 2/5; RAG chunks 3/5; schema compliance 2/5.

### `azure-stack-connect-azure-stack.md.json`

This document is partially successful. The parser selected `howto`, and the document does contain procedural material. Two of four units are known: `Connect to Azure Stack with Remote Desktop` and `Next steps`. The `Connect to Azure Stack with VPN` section remained unknown despite containing procedural and code content, probably because its construction mixes paragraphs, alerts, H3 headings, unordered lists, and code rather than a simple ordered-list procedure at the H2 level.

This document is ready for generic XML. The component-level preservation is good enough for a neutral XML output that keeps paragraphs, alerts, code, lists, and headings.

This document is marginal for DITA XML. The article type is plausible, but half the units are unknown and validation is false, so a DITA task output would need cleanup or improved unit decomposition.

This document is fairly usable for RAG. The unknown VPN section is important content, but the parser still preserves it as a coherent unit with components and source metadata.

Scores: XML 4/5; DITA XML 3/5; RAG chunks 3/5; schema compliance 2/5.

### `azure-stack-connect-vpn.md.json`

This document is the best fit for the current parser. The parser selected `howto`, and seven of eight units are known, including prerequisites and several procedure sections. The only unknown unit is the unnamed introductory block before the first H2.

This document is ready for generic XML. The parser preserved complex lists, nested inline attributes, tables, alerts, images, links, and source provenance.

This document is the closest to DITA XML readiness, but it is still not schema-compliant. The output has `validation.valid: false`; observed causes include a prerequisites unit emitted with `information_type: concept` where the schema expects `fact`, procedure units that the validator reports as invalid under the unit schema, and an unnamed unknown introduction unit.

This document is strong for RAG chunking. The H2 units align with task phases, ordered lists are preserved, and unit labels are mostly useful. It would benefit from turning the leading unnamed block into an introduction unit and resolving references.

Scores: XML 5/5; DITA XML 3/5; RAG chunks 4/5; schema compliance 3/5.

### `azure-stack-considerations.md.json`

This document is useful but semantically mismatched. The source topic is `overview`, while the parser selected `howto` with mixed information type. Three of six units are known: `Overview`, `Version requirements`, and `Next steps`. The comparison-oriented sections `Cheat sheet: High-level differences` and `Helpful tools and best practices` remained unknown even though they are structurally meaningful.

This document is ready for generic XML. The parser retained the overview text, tables, alert, code block, list, metadata, and references.

This document is weak for DITA XML as produced. A DITA topic, concept, overview, or reference-style mapping would fit better than how-to, and the schema validator rejects the current how-to output.

This document is usable for RAG with moderate cleanup. The main overview and requirements sections are labeled, but comparison tables and best-practice sections need known unit types to become strong metadata-rich chunks.

Scores: XML 4/5; DITA XML 2/5; RAG chunks 3/5; schema compliance 2/5.

## Cross-Document Findings

### Parser Strengths

The parser preserved content and structure across the full sample. It extracted titles, Microsoft Docs front matter, references, H2 unit boundaries, component types, inline attributes, tables, lists, images, code blocks, alerts, and source provenance where available.

The parser produced usable segmentation for RAG even when semantic classification was incomplete. Unknown units are still preserved as chunks with titles and component content, which is preferable to losing content or collapsing the whole article into an unstructured blob.

The parser recognized procedural construction well when headings and ordered lists were explicit. The VPN article demonstrates that the current model performs well on task-shaped content with clear procedure headings.

### Parser Weaknesses

The article classifier overweights procedure-like signals. A single `Next steps` section or action-oriented heading can pull conceptual, overview, or index-like documents into `howto`, even when source metadata says `conceptual`, `overview`, or `article`.

The unit classifier does not yet recognize common Microsoft Docs patterns. Headings such as `Cheat sheet`, `API version`, `Helpful tools and best practices`, `Before creating a VM`, and template/example names should likely map to `reference`, `fact`, `concept`, `overview`, or `link-related` units instead of `unknown`.

The leading content before the first H2 regularly becomes an unnamed `unitUnknown`. For these documents, that block is usually an introduction or applies-to note and should be classified as `introduction` or metadata-like content.

The schema and runtime model are not fully aligned. The JSON output contains fields such as `procedure_representation`, but validation diagnostics display alias-form objects and still reject procedure units. The prerequisites unit also emits `informationType: concept`, while `unitPrerequisites.schema.json` requires `fact`.

Reference resolution was not attempted in these outputs. Every reference state observed was `not_attempted`, so the files are not yet ready for link-integrity-sensitive publishing or retrieval workflows that depend on resolved local targets.

## Conversion Readiness

### Generic XML

The parsed files are generally ready for generic XML serialization. The parser has enough structural information to emit an XML hierarchy such as article, metadata, unit, component, attribute, reference, and diagnostic elements.

The XML output should preserve unknown classifications explicitly. Unknown article or unit labels should not be hidden during XML conversion, because they are the primary signal that the semantic layer needs more tuning.

Overall XML readiness: 4/5.

### DITA XML

The parsed files are not yet ready for trustworthy DITA XML conversion as semantic DITA topics. The readiness evaluator marks all six files as `dita:ready`, but schema validation fails for every file and several article types are likely wrong.

The safest DITA strategy today would be degraded output. The converter could emit generic DITA `topic` output for uncertain documents and reserve `task` or specialized how-to output for files like `azure-stack-connect-vpn.md.json` after schema alignment issues are fixed.

Overall DITA XML readiness: 2/5.

### Metadata-Rich RAG Chunks

The parsed files are mostly usable for RAG chunking. Each file has a title, front matter metadata, units, components, and no parse errors, so chunks can be generated with source path, title, article type, unit title, unit type, information type, component text, and diagnostics.

The chunk metadata quality is uneven. Documents with many unknown units should include `triage_status` and diagnostic codes in chunk metadata so retrieval consumers can distinguish trusted semantic chunks from structurally preserved but weakly classified chunks.

Overall RAG chunk readiness: 3/5.

## Standards Compliance

The files are not compliant with the current article schema standard. All six files report `validation.valid: false`, and every file has SP-030 schema warnings.

The files are partially compliant with the structural parsing standard. The Article → Unit → Component → Attribute hierarchy exists in every file, and the parser preserved content rather than dropping unknown material.

The files are weakly compliant with the semantic classification standard. Unknown-unit rates range from 12.5% in the VPN article to 88.9% in the ARM templates article, and every file is classified as `howto` despite mixed source metadata.

## Recommendations

The classifier should map Microsoft Docs metadata into the article triage decision. Values such as `ms.topic: conceptual`, `ms.topic: overview`, and `ms.topic: article` should be treated as metadata signals alongside `articleType`, `article_type`, and `type`.

The article signature scoring should reduce the weight of `Next steps`. A `Next steps` unit should support a how-to classification only when other procedure evidence is present; by itself it should not pull an overview, reference, or concept article into `howto`.

The unit title map should add Microsoft Docs headings. Candidate mappings include `Cheat sheet` to reference/fact, `API version` to reference/fact, `Helpful tools and best practices` to reference or principle, `Before creating` to prerequisites or concept depending on construction, and template names to reference/link units.

The classifier should classify pre-H2 body content as introduction when the document has an H1/title and the content consists of applies-to notes or opening paragraphs. This would remove a recurring source of `unitUnknown` diagnostics.

The schema and model should be tuned together. In particular, `unitPrerequisites` should either accept the runtime `concept` information type or the runtime should emit `fact`; procedure unit validation should be checked against the serialized field aliases used by the validator.

The pipeline should rerun these files with local reference resolution enabled before publication assessment. DITA XML and RAG workflows both benefit from resolved links and image targets, and the current outputs show only `not_attempted` reference states.

## Bottom Line

The parser worked well as a loss-preserving structural parser and moderately well as a RAG segmentation engine. The parser did not yet produce schema-compliant Structured Markdown articles for this sample, and it is not yet reliable enough to drive semantic DITA XML without either degraded topic output or classifier/schema tuning.
