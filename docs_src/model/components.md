# Component Types

A component is a block-level construct — the atomic building block of a unit. Each component maps to one or more Markdown block elements or HTML5 block elements, and each carries a `compType` field that identifies its kind. Text-bearing components (paragraphs, list items, table cells, headings) contain an ordered `content` array of attribute objects that represent the inline spans within the block. Structure-bearing components (lists, tables) contain an ordered `content` array of child components that represent their rows or items. The parser assigns a component type by inspecting the block element's Markdown syntax or HTML tag, then populating the component object with the fields defined in `componentShared.schema.json` and the type's own schema.

## Component Reference Table

| Component | Markdown Source | HTML Equivalent | Notes |
|---|---|---|---|
| compHeaderH1 | `# Heading` | `<h1>` | Document title |
| compHeaderH2 | `## Heading` | `<h2>` | Unit boundary |
| compHeaderH3 | `### Heading` | `<h3>` | Subsection |
| compHeaderH4–H6 | `#### ...` | `<h4>`–`<h6>` | Deep subsections |
| compParagraph | prose text | `<p>` | Contains attributes |
| compBlockCode | ` ```lang ` | `<pre><code>` | Fenced, with language tag |
| compBlockQuote | `> text` | `<blockquote>` | Generic quote |
| compAlertNote | `> [!NOTE]` | div.alert-info | GitHub-style alert |
| compAlertTip | `> [!TIP]` | div.alert-success | |
| compAlertImportant | `> [!IMPORTANT]` | div.alert-primary | |
| compAlertWarning | `> [!WARNING]` | div.alert-warning | |
| compAlertCaution | `> [!CAUTION]` | div.alert-danger | |
| compListOrdered | `1. item` | `<ol>` | Contains compListItem |
| compListUnordered | `- item` | `<ul>` | Contains compListItem |
| compListItem | list item | `<li>` | Child of list only |
| compTable | table | `<table>` | Contains compTableRow |
| compTableRow | table row | `<tr>` | thead/tbody role |
| compTableCell | table cell | `<th>` / `<td>` | column-index, colspan, rowspan |
| compLink | standalone link | `<a>` | |
| compUnknown | (any unmatched) | (varies) | Fallback |

## Heading Components

Heading components (`compHeaderH1` through `compHeaderH6`) represent the six levels of Markdown and HTML headings. The parser uses H2 headings specifically as unit boundaries — an H2 heading triggers the creation of a new unit, and the heading itself becomes the first component in that unit's `content` array. H1 headings typically appear only once per document as the document title and are represented as `compHeaderH1`. H3 through H6 headings create subsections within a unit and do not trigger unit boundaries. All heading components contain an attribute array for their inline content, supporting formatted heading text such as inline code or links.

## Paragraph and Code Components

The `compParagraph` component represents a block of prose text. It is the most common component type and appears in virtually every unit. Its `content` array holds the inline attribute objects that make up the paragraph's text — plain text spans, bold, emphasis, links, inline code, and so on. The `compBlockCode` component represents a fenced code block. It carries the `language` field populated from the info string following the opening fence (for example, `python` in ` ```python `). Code block content is treated as verbatim text — the parser does not further classify inline spans within a code block, because inline Markdown syntax inside a code fence is not interpreted.

## Blockquote and Alert Components

The `compBlockQuote` component represents a generic blockquote (`> text`). When a blockquote's first line matches the GitHub Flavored Markdown alert pattern (`> [!TYPE]`), the parser classifies it as one of the five alert specializations instead of the generic blockquote:

- **`compAlertNote`** — informational note; rendered as `div.alert-info`
- **`compAlertTip`** — helpful tip; rendered as `div.alert-success`
- **`compAlertImportant`** — important information the reader must not miss; rendered as `div.alert-primary`
- **`compAlertWarning`** — warning about potential negative consequences; rendered as `div.alert-warning`
- **`compAlertCaution`** — caution about dangerous or destructive actions; rendered as `div.alert-danger`

Alert specializations carry the same structure as `compBlockQuote` — an attribute array for the alert body — but their `compType` and rendered CSS class differ. The parent `compAlert` schema defines the shared fields; the five specialization schemas each set their own fixed `alertType` value.

## List Components and the Dependent Component Rule

The `compListOrdered` component represents a numbered list (`<ol>`); `compListUnordered` represents a bulleted list (`<ul>`). Both components contain a `content` array whose children must all be `compListItem` objects. The `compListItem` component is a dependent type: it is structurally valid only as a direct child of `compListOrdered` or `compListUnordered`. The schema enforces this constraint by defining `compListItem` as a valid `content` child only within the list component schemas — not at the unit level. This prevents malformed structures where list items appear outside lists, which would be unrenderable and would break round-trip fidelity to the source Markdown.

Each `compListItem` contains its own attribute array for the inline content of the list item. List items may contain formatted inline text (bold, code, links) but do not contain nested block elements such as paragraphs or nested lists — the model treats nested lists as a separate `compListOrdered` or `compListUnordered` sibling in the parent list's content array rather than as a child of a list item.

## Table Components and the Dependent Component Rule

The `compTable` component is the root of the table structure. It contains a `content` array of `compTableRow` objects. Each `compTableRow` carries a role field (`thead` or `tbody`) that indicates whether the row belongs to the table header or table body, and it contains a `content` array of `compTableCell` objects. Each `compTableCell` carries `columnIndex`, `colspan`, and `rowspan` fields and contains an attribute array for the cell's inline content. The cell role (`th` or `td`) is determined by the row's role: header rows produce `th` cells, body rows produce `td` cells.

The dependent component rules for tables enforce the same structural constraint as for lists: `compTableRow` is valid only inside `compTable`, and `compTableCell` is valid only inside `compTableRow`. These constraints are enforced at the schema level to prevent structural errors and to ensure that serializers and renderers can always assume a valid three-level table hierarchy.

## Platform Extension Components

The model includes five platform extension components that go beyond standard Markdown and HTML5 semantics. These components represent constructs specific to particular documentation platforms or content management systems.

- **`compBlueBox`** — a styled callout box used by some documentation platforms as a distinct visual element from standard alerts. It carries a `content` array of attribute objects for its body text.
- **`compColumns`** — a multi-column layout container. It carries a `content` array of column objects. Use this component when source HTML or platform-specific Markdown includes explicit column layout directives.
- **`compVideo`** — an embedded video element. It carries fields for the video source URL, poster image, and caption. The parser generates this component when it encounters a video embed directive or an HTML `<video>` element.
- **`compInclude`** — a file include directive that references another file by path. Documentation platforms that support content reuse via include directives produce this component. It carries a `filePath` field and optional overrides.
- **`compMetadata`** — a metadata block that carries structured data about the document or section but is not rendered as visible content. The parser generates this component from YAML front matter blocks, HTML `<meta>` elements embedded in the body, or platform-specific metadata directives.

## Fallback: compUnknown

The `compUnknown` component is the fallback for any block element that does not match a known component type. The parser assigns `compUnknown` when neither the Markdown syntax nor the HTML tag matches a known pattern. Content inside an unknown component is preserved verbatim in the `markdown` and `html` fields. Downstream tools can identify unknown components by their `compType` field and route them for inspection without losing any source content.
