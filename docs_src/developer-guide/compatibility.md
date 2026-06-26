# Compatibility

## Python Version Requirement

`structure_parser` requires Python 3.12 or later. The package relies on `StrEnum` behavior introduced in 3.11 and on `str | Path` union type syntax in function signatures that requires 3.10+; however, the test suite and CI configuration target 3.12 as the minimum supported version. Python 3.11 and earlier are not tested and are not supported.

## Pydantic Version Requirement

The package uses Pydantic v2 exclusively, requiring version 2.7 or later. Pydantic v1 is not supported: the `model_config = ConfigDict(frozen=True)` pattern used by `ParserConfig` and the `model_dump()` / `model_validate()` API are v2-only. If your project depends on Pydantic v1, you must upgrade before installing `structure_parser`.

## Key Dependency Versions

The following minimum versions are required and tested:

| Package | Minimum Version | Purpose |
|---|---|---|
| `markdown-it-py` | 3.0 | CommonMark token-stream parser used by `MarkdownAdapter` |
| `mdit-py-plugins` | 0.4 | Provides `front_matter_plugin` for YAML front matter extraction |
| `lxml` | 5.2 | C-accelerated HTML element tree used by `HtmlAdapter` |
| `jsonschema` | 4.22 | JSON Schema Draft 7 validation with `Draft7Validator` and `RefResolver` |
| `PyYAML` | 6.0 | Front matter deserialization via `yaml.safe_load` |
| `rich` | 13.7 | Terminal output formatting for the CLI |
| `typer` | 0.12 | CLI argument parsing |

`lxml` requires a compiled C extension. There is no pure-Python fallback: if `lxml` is absent or fails to import, `HtmlAdapter.parse()` raises `AdapterError` immediately with a message directing the user to install `lxml`.

## Platform Support

The package is developed and primarily tested on macOS (25.x). CI runs on Linux (Ubuntu). Windows is not explicitly tested but is expected to work for the core parsing API because no platform-specific system calls are used. File path handling uses `pathlib.Path` throughout, which normalizes separator differences. If you encounter a Windows-specific issue, please report it with the Python version, OS version, and a minimal reproducer.

## Schema Version Compatibility

All contract models carry a `schema_version` field that defaults to `"1"`. This is the only supported schema version. Future releases that introduce breaking changes to a contract's field structure will increment `schema_version` to `"2"` and provide explicit migration notes in the [Schema Versioning](schema-versioning.md) document. Downstream tools that consume parser output should check `schema_version` before processing and reject versions they do not recognize.

## Source Format Support

The parser supports two source formats in the current release:

| Extension | Format | Adapter |
|---|---|---|
| `.md`, `.markdown` | Markdown (CommonMark) | `MarkdownAdapter` |
| `.html`, `.htm` | HTML5 | `HtmlAdapter` |

DITA/XML parsing is deferred per assumption A-004. The `DitaXmlAdapter` recognizes `.dita`, `.ditamap`, and `.xml` extensions but raises `UnsupportedFormatError` immediately, which the parser converts to an SP-002 diagnostic. No DITA parsing occurs.

## Known Limitations

- **Cross-directory $ref resolution**: `jsonschema.RefResolver` does not reliably resolve `$ref` chains across multiple subdirectory levels when nested schemas use bare `$id` values. Affected documents receive an advisory SP-030 warning. See [Writing Validators](validators.md) for the planned migration to the `referencing` library.
- **Python 3.12+ StrEnum behavior**: The `domain/enums.py` enums rely on `StrEnum` comparisons that behave correctly in 3.12+. Earlier Python 3.11 behavior may differ subtly in membership tests.
- **lxml C extension required**: The HTML adapter has no pure-Python fallback. Environments that restrict native extensions cannot parse HTML source files.
- **No line numbers in HTML output**: `HtmlAdapter` does not record `start_line` or `end_line` on `RawNode` objects because lxml does not expose token-level line numbers for parsed HTML.
