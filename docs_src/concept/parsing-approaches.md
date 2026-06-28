# Parsing Approaches: AST, BNF, and Schema Mapping

Three broad approaches to parsing structured text have shaped how developers build Markdown processing pipelines: abstract syntax tree construction, formal grammar derivation, and deterministic schema mapping. `structure_parser` uses the third approach, and the choice is not arbitrary. Understanding why requires a careful look at what each approach produces, what it leaves unresolved, and what problem it is actually solving.

## The Abstract Syntax Tree Approach

Most Markdown parsers represent their output as an abstract syntax tree (AST), which faithfully captures the syntactic structure of the source without making any claim about its semantic meaning. An AST is a tree of nodes where each node has a type, a set of properties, and zero or more children. A Markdown document parsed into an AST becomes a root node containing heading nodes, paragraph nodes, list nodes, code block nodes, and blockquote nodes, each of which may contain inline nodes for emphasis, links, images, and text spans.

The CommonMark specification defines the syntax that most AST-based parsers implement. Parsers such as `cmark` (the reference C implementation), `marked` (JavaScript), and `markdown-it-py` (Python) all produce ASTs or token streams that conform to the CommonMark rules for heading levels, list nesting, code fences, and link syntax. The specification is precise enough that a heading node produced by `cmark` and a heading node produced by `markdown-it-py` carry the same information: the level (1 through 6) and the inline content of the heading.

An AST is a generic representation. A heading node at level 2 with the text "Prerequisites" carries its level and text, but not whether it introduces a concept definition, a procedure precondition, or a navigation landmark. The AST approach is powerful precisely because it is composable and format-neutral: transformation pipelines can walk the AST and emit HTML, PDF, slides, or any other output format without caring about what the content means. Remark plugins, Pandoc Lua filters, and mdast transformers all operate on this principle. The AST approach's limitation for semantic classification is equally clear: the AST is syntactically complete but semantically silent. Every semantic interpretation — "this heading introduces a procedure," "this blockquote is a warning" — requires a second pass that the AST itself cannot provide.

## Backus-Naur Form and Formal Grammars

Formal grammars, expressed in Backus-Naur Form (BNF) or its extensions, describe the syntactic production rules of a language and enable parser generators to produce deterministic parsers from those rules. BNF defines a language as a set of production rules that map non-terminal symbols to sequences of terminals and other non-terminals. A parser generated from a BNF grammar recognizes input strings that belong to the language and rejects those that do not, constructing a parse tree that reflects which production rules fired.

ANTLR, PEG parsers, and Earley parsers are all grammar-based tools used in language tooling, compilers, and format processors. The CommonMark specification uses a formal algorithmic description rather than pure BNF because Markdown's list parsing rules are context-sensitive in ways that pure BNF cannot represent — the indentation-sensitive list continuation rules depend on state that a context-free grammar cannot track. Despite this, CommonMark approximates BNF for most constructs, and the community has produced PEG grammars and formal descriptions of Markdown subsets for use in parser generators.

Grammar-based parsing is semantically neutral in the same way that AST parsing is. A BNF production rule for a level-2 heading (`## text`) tells the parser that a line beginning with two `#` characters followed by a space and text content is a level-2 heading. It cannot tell the parser whether that heading introduces a concept, a procedure step, or a reference section — those are semantic distinctions that exist outside the syntax of the language. Semantic interpretation always requires a second pass beyond the grammar, a layer that maps syntactic constructs to meaning. Grammar-based parsers are the right choice for language tooling, syntax highlighting, and format conversion, where the goal is syntactic recognition; they are the wrong starting point when the goal is semantic classification.

## The Deterministic Schema Mapping Approach

`structure_parser` uses a third approach — deterministic schema mapping — that bypasses the grammar-first pipeline in favor of mapping parsed constructs directly to a target schema. Rather than defining a grammar for Markdown and deriving a parse tree, the parser uses `markdown-it-py` to produce a token stream, converts it to a flat list of typed `RawNode` objects, and then classifies those nodes against the Article → Unit → Component → Attribute hierarchy using a set of deterministic pattern-matching rules.

The `RawNode` types are: `heading`, `paragraph`, `code_block`, `blockquote`, `list`, and `table`. These six types cover the structural vocabulary of Markdown. Once the adapter has produced a list of `RawNode` objects, the grammar is finished — `markdown-it-py` is not consulted again. The classifier in `structured_markdown/classifier.py` takes over and applies the following pattern-matching logic:

- The document is split into sections at H2 boundaries. Each section becomes a candidate Unit.
- The section heading's text is matched against a keyword table (`_UNIT_TITLE_MAP`). A heading whose text contains "Prerequisites" maps to `UnitType.prerequisites`; "Introduction" or "Overview" maps to `UnitType.introduction`; "Next Steps" maps to `UnitType.link_nextstep`.
- If the heading does not match any keyword, the section's body nodes are inspected for content shape: a section containing an ordered list is classified as `UnitType.procedure` with `ProcedureRepresentation.ordered_list`; a section containing only a fenced code block is classified as `UnitType.procedure` with `ProcedureRepresentation.code_block`.
- Each body node within a section is mapped to a Component type. A fenced code block becomes `compBlockCode`; a blockquote beginning with `[!NOTE]` becomes `compAlertNote`; a paragraph becomes `compParagraph`; an ordered list becomes `compListOrdered`.
- The article type is read from front matter first (`articleType`, `article_type`, or `type` key) and mapped against `_ARTICLE_TYPE_MAP`.
- If no supported metadata value is present, the classifier scores the inferred unit types against runtime article signatures that mirror the schema model's required and preferred unit populations.
- If a specialized signature wins, the classifier assigns that article type; if the document contains known units without a specialized match, it falls back to `ArticleType.topic`; if neither metadata nor construction provides a useful signal, `ArticleType.unknown` is assigned and an SP-041 diagnostic is emitted.

This approach is not general-purpose. It is purpose-built to map Markdown to a specific schema and produces useful results only for content that follows the conventions the schema expects. A Markdown document that uses heading levels unconventionally or organizes content in ways the classifier does not recognize will receive `unknown` triage status on the unclassified units and corresponding SP-040 diagnostics; if neither metadata nor construction identifies the article, it also receives SP-041 — but the parse will still complete and produce a partial structured result.

## The Tradeoffs of Each Approach

Each approach makes a different tradeoff between generality, composability, and semantic expressiveness, and the right choice depends on the problem the parser is solving.

AST parsers — `markdown-it-py`, remark, pandoc — are general-purpose tools. They are the right choice when the downstream consumer decides what structure means: a static site generator, a format converter, or a plugin pipeline that applies its own interpretation. They are the wrong choice when you need a guaranteed semantic contract in the output, because the AST provides no guarantee that "Introduction" means a Unit introduction or that a blockquote is a warning rather than an arbitrary quoted passage.

Grammar-based parsers — ANTLR grammars for Markdown, PEG parsers — are theoretically clean and composable. They are the right choice for language tooling, syntax highlighting, IDE integrations, and format conversion where syntactic correctness is the goal. They are the wrong choice for semantic classification because grammar and semantics are orthogonal: a grammar can tell you that a construct is syntactically valid; it cannot tell you what the construct means within an information architecture.

Schema mapping — `structure_parser`'s approach — is purpose-built and non-general. It is the right choice when:

- The target model is known in advance and stable (the Article → Unit → Component → Attribute hierarchy in `model/`).
- The authoring convention is consistent enough that pattern-matching rules classify most content correctly.
- Diagnostic feedback for non-conforming content is a first-class requirement, not an afterthought.

It is the wrong choice when the target model is not known in advance, when content conventions vary widely across sources, or when the schema changes frequently, because every change to the hierarchy potentially requires updating the classifier's pattern-matching rules.

## Comparison Table

| Approach | Output | General Purpose | Semantic Classification | Diagnostic Feedback | Example Tools |
|---|---|---|---|---|---|
| AST | Syntax tree | Yes | No | No | markdown-it-py, remark, cmark |
| BNF / formal grammar | Parse tree | Yes | No | Syntax errors only | ANTLR, PEG parsers |
| Schema mapping | Classified model | No | Yes | Yes (SP-NNN codes) | structure_parser |

## Design Position

`structure_parser` accepts the tradeoff of non-generality in exchange for a guaranteed, validated, diagnostic-annotated semantic output. The JSON schemas in `model/` are the target specification — they define what an `artHowto.schema.json` article must contain, what units a `unitProcedure.schema.json` unit may include, and what components a `compBlockCode.schema.json` component represents. The classification pipeline is the mechanism for reaching that specification from a plain Markdown source. The result is a `StructuredContent` model with an assigned article type, a list of typed units, typed components within each unit, and a diagnostic list that explains every classification decision that could not be made with full confidence. The tradeoff is explicit and bounded: the parser knows its target schema, classifies what it can, and names what it cannot — and that combination of specificity, coverage, and honesty is what the schema mapping approach makes possible.
