# Attribute Types

An attribute is an inline element within a text-bearing component. Attributes are the leaf nodes of the four-level hierarchy — they carry the actual text content, links, images, and inline formatting that authors write. Where components are block-level (paragraphs, lists, tables), attributes are span-level: they exist inside components, not alongside them. The parser generates attribute objects by walking the inline AST of each text-bearing component and classifying each inline node by its Markdown syntax or HTML tag. The resulting attribute array preserves the source order of inline spans and captures both the structured representation (typed fields) and the raw source forms (the `markdown` and `html` fields inherited from `attributeBase`).

## The attributeBase Contract

Every attribute schema extends `attributeShared.schema.json`, which defines the `attributeBase` object. This shared contract guarantees a consistent set of fields across all attribute types:

- **`attType`** — the string identifier for the attribute type (for example, `attText`, `attLink`, `attCode`).
- **`markdown`** — the raw Markdown source text that produced this attribute span (for example, `` `code` `` for an inline code span).
- **`html`** — the rendered HTML form of the attribute span (for example, `<code>code</code>`).
- **`text`** — the plain text content of the span, with all markup stripped. This field is used by search indexers, accessibility validators, and plain-text exporters.
- **`metadata`** — an open object for downstream tools to attach arbitrary annotations without modifying the structural contract.
- **`provenance`** — a provenance object that records the source location (line and character offset) of the inline span within the original document.

The `sharedInLineElementProperties.schema.json` companion schema defines the shared inline property definitions that concrete attribute schemas reference.

## Attribute Reference Table

| Attribute | Markdown Source | HTML Equivalent | Key Fields |
|---|---|---|---|
| attText | plain text | (text node) | text |
| attStrong | `**text**` or `__text__` | `<strong>` | markdown, text |
| attBold | `**text**` | `<b>` | markdown, text |
| attEmphasis | `*text*` or `_text_` | `<em>` | markdown, text |
| attItalic | `*text*` | `<i>` | markdown, text |
| attCode | `` `code` `` | `<code>` | markdown, text |
| attLink | `[text](href)` | `<a href="">` | href, text |
| attAnchor | `<a name="">` | `<a>` | target |
| attImage | `![alt](src)` | `<img>` | source, altText |
| attSpan | `<span>` | `<span>` | content (array of attributes) |
| attSub | `<sub>` | `<sub>` | text |
| attSuper | `<sup>` | `<sup>` | text |
| attUnknown | (any unmatched) | (varies) | Fallback |

## Semantic vs. Presentational Inline Formatting

The model distinguishes between semantic and presentational forms of bold and italic formatting because HTML sources can use either, and the distinction carries meaning for downstream processing.

**`attStrong`** maps to the `<strong>` element and Markdown's `**text**` or `__text__` syntax. It signals strong importance — the browser and screen reader interpret it as semantically significant. **`attBold`** maps to the `<b>` element and the same Markdown syntax when the source HTML explicitly uses `<b>`. It signals visual boldness without the semantic weight of importance. When the parser encounters Markdown `**text**`, it produces `attStrong` by default; when it encounters an HTML `<b>` element in an HTML source, it produces `attBold`.

The same distinction applies to emphasis and italic. **`attEmphasis`** maps to `<em>` and signals semantic emphasis (stress, title of a work, foreign phrase). **`attItalic`** maps to `<i>` and signals visual italics without semantic stress. Markdown `*text*` or `_text_` produces `attEmphasis`; HTML `<i>` produces `attItalic`. This separation allows accessibility validators and semantic linters to flag cases where a visual form was used in a context that warrants the semantic form, and it preserves round-trip fidelity when serializing back to HTML.

## attLink and Reference Classification

The `attLink` attribute represents a hyperlink. It carries two key fields beyond `attributeBase`: **`href`** (the URL or relative path the link points to) and **`text`** (the link's display text). The reference classifier in the `structure_parser` package walks the attribute arrays of every text-bearing component to collect all `attLink` objects. This walk produces the document's full link inventory, which the classifier uses to detect broken links, classify internal vs. external references, and populate link-related unit types (`unitLinkNextstep`, `unitLinkRelated`). The `href` field is the primary input to these link-resolution routines, making `attLink` one of the most structurally significant attribute types for downstream processing.

## attImage and Accessibility Validation

The `attImage` attribute represents an inline image. It carries **`source`** (the image URL or relative path) and **`altText`** (the alternative text for the image). The `altText` field is the primary input to the accessibility validator, which checks that every image has non-empty alternative text and flags violations as metadata annotations on the attribute object. The `source` field feeds the reference classifier's asset inventory, which tracks all image dependencies of a document for build-system integration.

## attAnchor: Navigation Targets

The `attAnchor` attribute represents an anchor target — an HTML `<a name="">` element that defines a named location in the document. It carries a **`target`** field containing the anchor name. The `attAnchor` type is distinct from `attLink`: a link navigates to a location, while an anchor defines one. The reference classifier uses the anchor inventory to validate that all internal fragment links (`href="#section"`) resolve to a defined anchor or heading ID within the document.

## attSpan: Nested Inline Containers

The `attSpan` attribute represents a generic inline container — an HTML `<span>` element. Unlike the other attribute types, which carry scalar text content, `attSpan` carries a **`content`** array that holds nested attribute objects. This nesting supports inline spans that contain multiple formatted children: for example, a `<span>` that wraps both bold text and a link would produce an `attSpan` whose `content` array contains an `attStrong` and an `attLink`. The `attSpan` type is most common in HTML-sourced content, where `<span>` elements are used for styling, language tagging, or custom data attributes. The `attSpan`'s `content` array follows the same attribute classification rules as the parent component's `content` array.

## attUnknown: Fallback for Unclassifiable Inline Constructs

The `attUnknown` attribute is the fallback for any inline element that does not match a known attribute type. The parser assigns `attUnknown` when the inline node's Markdown syntax or HTML tag does not correspond to any concrete attribute schema. The raw source is preserved in the `markdown` and `html` fields, and the `text` field holds the plain-text extraction. Downstream tools can identify unknown attributes by their `attType` field and route them for inspection without discarding any content from the source document.
