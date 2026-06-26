# Writing Adapters

## Adapter Responsibility

An adapter's sole job is to convert a source file into a `RawParseModel` — a typed list of `RawNode` objects plus a parsed front matter dictionary. Adapters perform no classification, enrichment, or validation. They translate syntax into a neutral intermediate form that downstream pipeline stages (the classifier, enricher, and validator) can consume without knowing anything about the source format. This strict boundary keeps format-specific code isolated and makes adding a new adapter straightforward.

## The IFormatAdapter Protocol

The `IFormatAdapter` protocol, defined in `adapters/base.py`, specifies the contract every adapter must satisfy:

```python
class IFormatAdapter(Protocol):
    source_format: str
    supported_extensions: tuple[str, ...]

    def parse(self, path: Path, config: ParserConfig) -> RawParseModel: ...
```

The `source_format` attribute is a lowercase string identifier such as `"markdown"` or `"html5"`. The `supported_extensions` tuple lists the file suffixes the adapter claims, such as `(".md", ".markdown")`. The `parse` method receives the absolute file path and the current `ParserConfig`; it returns a `RawParseModel` or raises `AdapterError` on unrecoverable failure. Adapters must not raise any other exception type.

## The RawNode Contract

`RawNode` (defined in `contracts/raw.py`) is the unit of adapter output. Every structural or inline element in the source document becomes one `RawNode`. The fields are:

| Field | Type | Purpose |
|---|---|---|
| `node_type` | `str` | Semantic type: `"heading"`, `"paragraph"`, `"list"`, `"list_item"`, `"code_block"`, `"blockquote"`, `"table"`, `"table_row"`, `"table_cell"`, `"hr"`, `"html_block"`, `"image"`, `"link"`, `"text"`, `"softbreak"`, `"hardbreak"`, `"em"`, `"strong"`, `"code_inline"`, `"front_matter"` |
| `tag` | `str` | HTML tag equivalent: `"h1"`, `"p"`, `"ul"`, `"ol"`, `"li"`, `"pre"`, `"blockquote"`, `"table"`, `"tr"`, `"td"`, `"th"`, `"hr"`, `"a"`, `"img"`, `"strong"`, `"em"`, `"code"` |
| `content` | `str` | Raw text or Markdown source for the node |
| `children` | `list[RawNode]` | Nested nodes: inline children of paragraphs, items in lists, rows in tables |
| `attrs` | `dict[str, Any]` | Format-specific attributes: `href`, `src`, `alt`, `language`, `level`, `alert_type`, `row_role`, `cell_role` |
| `start_line` | `int \| None` | 1-based source line where the node begins (when available) |
| `end_line` | `int \| None` | 1-based source line where the node ends (when available) |
| `level` | `int \| None` | Heading level 1–6; `None` for non-heading nodes |

## The RawParseModel Contract

`RawParseModel` wraps the full adapter output for one file. Its fields are:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | `str` | Always `"1"` |
| `source_format` | `SourceFormat` | Enum value set by the adapter |
| `source_path` | `str` | Absolute path string of the parsed file |
| `content_hash` | `str \| None` | SHA-256 hex digest of the raw file content |
| `front_matter` | `dict[str, Any]` | Parsed YAML front matter as a dict; empty dict if absent |
| `front_matter_raw` | `str \| None` | Raw unparsed YAML string for diagnostics |
| `front_matter_error` | `str \| None` | Parse error string if front matter was malformed |
| `nodes` | `list[RawNode]` | Ordered list of top-level raw nodes |
| `parse_errors` | `list[str]` | Non-fatal parse error strings accumulated during parsing |

## The Markdown Adapter

The `MarkdownAdapter` (in `adapters/markdown.py`) uses markdown-it-py's CommonMark parser with the `front_matter_plugin` and the `table` extension enabled. Parsing proceeds in two phases. First, the adapter calls `MarkdownIt.parse()` on the raw source string, which returns a flat token list. Second, the internal `_tokens_to_nodes()` function walks that token list and emits `RawNode` objects.

Block-level token pairs — such as `heading_open`/`heading_close`, `paragraph_open`/`paragraph_close`, and `bullet_list_open`/`bullet_list_close` — are consumed as units: the adapter advances its index past the matching close token and captures any nested `inline` token in between. The inline token's children are recursively converted by `_inline_tokens_to_nodes()`, which handles `text`, `softbreak`, `hardbreak`, `strong_open`/`strong_close`, `em_open`/`em_close`, `code_inline`, `link_open`/`link_close`, and `image`. Fenced code blocks (`fence` tokens) capture the language tag from `tok.info`. Blockquotes run a secondary regex scan over their inner inline tokens to detect GitHub Alert syntax: lines matching `[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, or `[!CAUTION]` set an `alert_type` attribute on the blockquote node. Tables are decomposed into `table_row` and `table_cell` nodes, with `row_role` set to `"header"` inside a `thead` section and `"body"` inside `tbody`. Line number information comes from `tok.map`, which markdown-it records for block tokens; inline nodes do not carry independent line ranges.

## The HTML Adapter

The `HtmlAdapter` (in `adapters/html.py`) uses `lxml.html.fromstring()` to parse an HTML string into an element tree. The adapter traverses the element tree starting from the `<body>` element (or the document root if no body is present) and maps elements to `RawNode` objects using the same `node_type` vocabulary as the Markdown adapter. Heading elements `h1`–`h6` become `"heading"` nodes with the `level` field set. Paragraphs, fenced code equivalents (`pre`/`code`), lists, blockquotes, and tables follow the same structural mapping. Container elements such as `div`, `section`, `article`, and `main` are traversed transparently — their children are emitted directly without a wrapping node. Script, style, nav, and footer elements are silently dropped. Because lxml does not expose token-level line numbers for parsed HTML, `start_line` and `end_line` are always `None` in HTML adapter output.

## Registering a New Adapter

To add support for a new source format:

1. Create a class in `adapters/` that satisfies the `IFormatAdapter` protocol: set `source_format`, populate `supported_extensions`, and implement `parse()`.
2. Import the class in `application/adapter_registry.py` and add an instance to the `_build_registry()` call alongside `MarkdownAdapter()`, `HtmlAdapter()`, and `DitaXmlAdapter()`.
3. Add the new `SourceFormat` enum value to `domain/enums.py` if one does not already exist.
4. Add a fixture file and unit tests in `tests/unit/test_<format>_adapter.py`.

The `AdapterRegistry.get_adapter()` function resolves the adapter by file extension first, then applies the `config.source_format` override if one is set. That override allows callers to force a specific adapter regardless of file extension — useful for testing or for files with non-standard extensions.

## The DITA Adapter Stub

`DitaXmlAdapter` (in `adapters/dita_xml.py`) claims the `.dita`, `.ditamap`, and `.xml` extensions but raises `UnsupportedFormatError` unconditionally from its `parse()` method. This satisfies the registry contract — the format is recognized — while immediately communicating that DITA parsing is deferred per assumption A-004. Callers receive an SP-002 diagnostic rather than an unhandled Python exception, and the parse run continues with any remaining files.

## Source Format Auto-Detection

When `ParserConfig.source_format` is `None` (the default), the registry selects an adapter by file extension: `.md` and `.markdown` map to `MarkdownAdapter`; `.html` and `.htm` map to `HtmlAdapter`. To override auto-detection, set `source_format` explicitly:

```python
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig
from structure_parser.domain.enums import SourceFormat

config = ParserConfig(source_format=SourceFormat.markdown)
doc = parse_file("article.txt", config=config)
```

Files with unrecognized extensions and no `source_format` override produce an SP-002 diagnostic and a `ParsedDocument` with `has_errors=True`.
