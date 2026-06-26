# Comparison with Similar Approaches

`structure_parser` occupies a specific position in the landscape of tools that process, validate, or publish Markdown and structured content. Understanding that position requires a clear-eyed look at what adjacent tools do, where they succeed, and where they stop short of what Structured Markdown provides. The comparison below covers seven categories of tools and ends with a table that makes the tradeoffs explicit.

## DITA and the DITA Open Toolkit

DITA is the most fully realized semantic authoring system in wide use for technical documentation. Every element in a DITA document carries a schema contract enforced by a DTD or RELAX NG schema at authoring time: a `<task>` element must contain a `<taskbody>`; a `<taskbody>` must contain `<steps>`; each `<step>` must contain a `<cmd>`. A document that violates these constraints fails schema validation before it enters any publishing pipeline. This schema-first enforcement is DITA's core strength: transformation pipelines can process `<task>` elements knowing exactly what structure they will find, without inspecting content.

The DITA Open Toolkit (DITA-OT) is the reference publishing engine for DITA content. It processes conforming DITA XML into HTML, PDF, EPUB, and help systems, exploiting the guaranteed structural contracts that DITA's schemas establish. The machine-processability of DITA output is as high as any open standard achieves: a downstream tool that can read a DITA topic type can make structural decisions — numbered steps, conditional text, conref resolution — purely from schema knowledge.

The cost of this power is well-documented. DITA requires specialized XML editors such as oXygen XML Editor, XMetaL, or Arbortext because raw XML authoring is error-prone and slow. Authors must understand topic specialization, the difference between `<concept>` and `<task>`, when to use `<note>` versus `<hazardstatement>`, and how to manage reuse through keyrefs and conrefs. The DITA-OT itself requires maintenance and configuration per output target. The authoring friction is not a failure of DITA — it is the direct consequence of enforcing a semantic contract at the source. Structured Markdown defers that enforcement to the parser rather than the editor, which is what makes its authoring friction low.

## Static Site Generators: Docusaurus, MkDocs, Hugo, Jekyll

Static site generators transform Markdown source into published websites. Docusaurus, MkDocs, Hugo, and Jekyll all support Markdown input and add navigation structure, theming, search, and deployment pipelines on top of it. They handle Markdown well for what they are designed to do: produce publishable HTML from source files with minimal configuration.

None of these tools classify Markdown content semantically. They treat all Markdown files identically: a heading is a heading, a paragraph is a paragraph, a code block is a code block. The tools may read front matter fields like `title` and `date` for navigation purposes, but they do not interpret `articleType: howto` as a semantic contract, do not validate whether a howto article has the expected sections, and do not produce structured output that downstream systems can process without re-reading the Markdown. They are publishing tools, not structured content pipelines.

The limitation is not a gap in these tools so much as a difference in purpose. A static site generator answers the question "how do I publish this Markdown as a website?" Structured Markdown answers the question "what is this Markdown about, and does it conform to a content model?" The two questions are orthogonal — a Docusaurus site can be built from content that `structure_parser` has validated, and `structure_parser` output can be used to drive a documentation site — but the tools are not in competition on the same axis.

## Pandoc

Pandoc is a universal document converter that reads dozens of input formats and writes dozens of output formats. Its internal representation is a rich AST that captures the syntactic structure of the source with high fidelity. Pandoc excels at format translation: converting Markdown to LaTeX, DOCX, EPUB, HTML, or RST with a single command. Its Lua filter system allows arbitrary AST transformations during conversion.

Pandoc does not classify content semantically and does not produce diagnostic feedback about content structure. Its AST knows that a node is a heading of level 2, but it does not know whether that heading introduces a concept definition, a procedure, or a reference section. Pandoc does not implement the Horn information types, DITA topic types, or any other information architecture. It is a format converter, and a very capable one, but it is not a structured content classifier. A Pandoc conversion pipeline that needs to produce DITA output must implement its own classification logic on top of the Pandoc AST — `structure_parser` implements that classification as its primary function.

## Markdoc

Markdoc is an extended Markdown dialect developed by Stripe that adds a compile-time AST transformation system to Markdown. It supports custom node syntax such as `{% callout type="warning" %}` that allows authors to add semantic annotations directly in the source. Markdoc processes these custom tags at compile time, transforming them into React components, HTML elements, or other output formats.

Markdoc's approach is more semantically expressive than plain Markdown because it allows authors to annotate content with explicit type information. Its limitation is that it requires authors to learn and use a custom tag syntax, which raises the authoring friction above plain Markdown and makes Markdoc source files non-portable: they render correctly only in Markdoc-aware environments. Markdoc also does not implement an information architecture — it provides a mechanism for semantic annotation but not a vocabulary of content types. An author using Markdoc must define what `{% callout %}`, `{% procedure %}`, and `{% definition %}` mean, and enforce that vocabulary through tooling they build themselves. Structured Markdown provides the vocabulary (Article, Unit, Component types) and the enforcement (the parser and the JSON schemas in `model/`) as first-class deliverables.

## Vale

Vale is a prose linter for technical writing that checks documents against configurable style rules defined in YAML. It operates at the sentence and word level, checking for passive voice, word choice, comma usage, term consistency, and similar writing quality concerns. Vale is widely used in documentation teams as a CI-enforced style gate.

Vale is complementary to `structure_parser`, not equivalent to it. Vale operates at the prose level and has no concept of document structure, content type, or information architecture. It cannot tell you whether a document is a howto or a reference article, whether an expected section is missing, or whether a procedure is represented as an ordered list. `structure_parser` operates at the structural level and has no concept of prose quality, word choice, or sentence construction. The two tools address different aspects of documentation quality and can be run together in the same CI pipeline without conflict.

## Diátaxis

Diátaxis (the Divio documentation system) is a documentation philosophy, not a parser or a tool. It defines four documentation types — tutorials, how-to guides, explanations, and reference — each serving a distinct reader need and requiring distinct authoring conventions. Diátaxis is widely cited in the technical writing community as a principled framework for organizing documentation.

Diátaxis is structurally similar to the Horn/DITA classification layer in Structured Markdown: both identify a vocabulary of content types and describe when each type is appropriate. The key difference is that Diátaxis is a conceptual framework with no machine enforcement. An author can label a page "How-to Guide" and write a tutorial; nothing in Diátaxis objects. `structure_parser` can be understood as a machine-implementable subset of Diátaxis-style thinking — it enforces a type vocabulary at parse time, emits diagnostics when content does not conform, and produces structured output that downstream tools can use. Diátaxis names the intellectual categories; Structured Markdown operationalizes a subset of them.

## mdast and the unified/remark Ecosystem

The unified/remark ecosystem provides a rich plugin-based pipeline for processing Markdown through abstract syntax trees (mdast). The mdast specification defines a tree of node types — heading, paragraph, code, list, image, link — that captures the syntactic structure of Markdown with high fidelity. The remark plugin ecosystem includes hundreds of plugins for linting, transformation, and output generation.

The mdast approach captures structure but not semantic classification. An mdast heading node carries its depth and content; it does not carry a unit type, information type, or schema identity. The remark ecosystem does not implement Horn information types, DITA topic types, or Article → Unit → Component → Attribute hierarchies. Building a Structured Markdown classifier on top of mdast is possible — it would require a custom plugin that walks the mdast tree and applies the same classification rules `structure_parser` uses — but this is not a built-in capability of the ecosystem. The unified/remark tools are a strong foundation for Markdown processing pipelines; they are not a semantic classification system.

## Summary Table

| Approach | Semantic Contract | Author Friction | Machine-Processable | Diagnostic Feedback | Markdown Source |
|---|---|---|---|---|---|
| DITA + DITA-OT | Full (schema-first) | High | Yes | Yes (schema errors) | No (XML) |
| Static site generators | None | Low | No | No | Yes |
| Pandoc | None | Low | Partial (AST) | No | Yes (input) |
| Markdoc | Partial (custom tags) | Medium | Partial | Compile errors | Extended Markdown |
| Vale | Style only | Low | No | Yes (style) | Yes |
| Diátaxis | Conceptual only | Low | No | No | Yes |
| mdast / unified | Structure only | Low | Partial (AST) | No | Yes |
| **Structured Markdown** | Pattern language | Low (authoring) / Medium (conformance) | Yes (classified output) | Yes (SP-NNN codes) | Yes |

## The Positioning Claim

Structured Markdown occupies a niche that no existing tool covers: low-friction Markdown authoring with machine-processable semantic output and author-facing diagnostics. Plain Markdown and static site generators preserve authoring ease but produce no semantic contract. DITA provides a full semantic contract but imposes XML authoring. Markdoc extends Markdown with semantic tags but requires a custom vocabulary and non-portable source. No tool in the landscape above produces classified, schema-validated, diagnostic-annotated structured output from plain Markdown source without altering the source format. The tradeoff that makes this possible is that the contract is not enforced at authoring time. An author can write Markdown that does not conform to the Structured Markdown pattern language, and the format will not object. The parser closes the loop: it classifies what it can, emits SP-NNN diagnostics for what it cannot, and produces a structured result regardless. In a team with CI/CD enforcement of diagnostics, this approximates schema-first guarantees. In a team without pipeline discipline, it provides best-effort enrichment. Whether that tradeoff is acceptable depends on the authoring environment, but the niche it occupies is real, and no other tool in this list fills it.
