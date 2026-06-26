# Testing

## Test Architecture

The test suite is organized in three layers: unit tests that verify individual models and services in isolation, contract tests that assert the parser produces expected output for known fixture inputs, and integration tests that exercise the public API end-to-end. This layering means a broken adapter surfaces in unit tests before it ever reaches the integration layer, and a broken public API surface is caught even if all lower layers pass. As of v0.1.0, the suite contains 103 tests with zero failures.

## Unit Tests

Unit tests live in `tests/unit/` and test one class or function at a time with no file I/O except for the adapter tests, which read fixture `.md` or `.html` files.

**`test_contract_models.py`** verifies that all Pydantic contract models construct correctly from valid input, expose the correct defaults, and enforce immutability on frozen models. `ParserConfig` is frozen, so tests confirm that assignment after construction raises `ValidationError`. `ParsedDocument` computed properties (`has_errors`, `error_count`, `warning_count`) are tested with synthetic diagnostic lists.

**`test_diagnostic_factory.py`** calls every `DiagnosticFactory` class method and asserts the returned `Diagnostic` carries the correct SP-NNN code, severity, category, and a non-empty message string. The suite covers all 15 defined codes: SP-001 through SP-003, SP-010, SP-011, SP-020, SP-021, SP-030 through SP-032, SP-040, SP-041, SP-050, SP-060, and SP-099.

**`test_markdown_adapter.py`** passes inline Markdown strings directly to `MarkdownAdapter.parse()` via a temporary file and asserts the correct `RawNode` graph. Key cases include single and multi-level headings, paragraphs with inline children (bold, italic, inline code, links, images), fenced code blocks with and without a language tag, blockquotes with and without GitHub Alert syntax, ordered and unordered lists with nested sublists, and tables with header rows. The test also asserts that `RawParseModel.content_hash` is a 64-character hex string and that `start_line` values are populated correctly for block nodes.

**`test_structured_markdown_classifier.py`** tests the classifier service that converts a `RawParseModel` into a `StructuredContent` object, asserting correct `article_type`, `unit_type`, and `information_type` assignments for representative heading structures and front matter combinations.

**`test_reference_classifier.py`** tests link and image extraction, asserting that hyperlinks and image references found in paragraphs and inline children become `Reference` objects with the correct `ref_type` and `href` values.

**`test_local_file_resolver.py`** tests the `resolve_local_references: bool` path: when enabled, relative `href` values are resolved against the source file's parent directory, and `Reference.state` transitions from `not_attempted` to `resolved` or `unresolved`.

**`test_model_validator.py`** calls `validate_against_schema()` with both valid and invalid `StructuredContent` dicts and asserts that `ModelValidationResult.valid` is correct and that SP-030 diagnostics are present on failure.

**`test_transform_readiness.py`** tests readiness scoring for each supported target (`dita`, `schema-org`, `rag-ingestion`), asserting that a document missing required fields receives `blocked` and that a complete document receives `ready`.

## Contract Tests

Contract tests live in `tests/contract/` and are fixture-based: each test parses a known input file and asserts specific properties of the parser output, making regressions immediately visible without requiring full output comparison.

**`test_clean_fixture_contract.py`** parses `tests/fixtures/markdown/clean.md`, a well-formed how-to article with correct front matter, sequential headings, and no unresolved references. It asserts that `has_errors` is `False`, that `structured_content.article_type` is `"howto"`, that at least one procedure unit is present, and that `validation.valid` is `True`.

**`test_known_failure_fixture_contract.py`** parses `tests/fixtures/markdown/known_failure.md`, which intentionally skips a heading level. It asserts that `diagnostics` contains exactly one SP-021 entry with the correct `from_level` and `to_level` detail values.

**`test_unknown_classification_fixture_contract.py`** parses `tests/fixtures/markdown/unknown_classification.md`, a file with ambiguous structure that cannot be classified. It asserts the presence of SP-040 and SP-041 diagnostics and confirms that `structured_content.article_type` is `"unknown"`.

**`test_schema_generation.py`** invokes the generation logic from `tools/generate_json_schemas.py` and asserts that the generated JSON Schema files for `ParsedDocument`, `ParseRunResult`, `Diagnostic`, `Reference`, and `StructuredContent` are present and match the expected structure. This test fails when a contract field changes without the schema being regenerated.

## Integration Tests

Integration tests live in `tests/integration/` and call the public API functions directly, treating the package as an external consumer would.

**`test_parse_files_end_to_end.py`** exercises three scenarios:

1. `parse_file()` on a well-formed fixture returns a `ParsedDocument` with `source_path` set, `source_format` as `SourceFormat.markdown`, and no error-severity diagnostics.
2. `parse_files()` on a list of three fixture paths returns a `ParseRunResult` with `stats.file_count == 3`, a non-zero `stats.duration_ms`, and one `ParsedDocument` per path in the same order.
3. `parse_file()` on a non-existent path returns a `ParsedDocument` with an SP-001 diagnostic and `has_errors == True` without raising a Python exception.

## Running the Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=structure_parser --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only contract tests
pytest tests/contract/

# Run only integration tests
pytest tests/integration/
```

## Developer Tools

Three tools in `tools/` support the contract test workflow.

**`tools/validate_fixtures.py`** runs every file in `tests/fixtures/` through the parser and prints a pass/fail table. A fixture passes when the result contains no SP-099 (internal error) diagnostics. Run this after any pipeline change to catch regressions before running the full test suite.

**`tools/update_expected_contracts.py`** regenerates the expected JSON output files stored alongside fixtures. Run this after an intentional contract change — such as adding a new field or changing classifier behavior — to update the baseline before running the contract tests.

**`tools/generate_json_schemas.py`** regenerates the JSON Schema artifacts in `schemas/parser/v1/` and `schemas/structured_markdown/v1/` from the current Pydantic models. Run this after adding or removing fields on any contract model:

```bash
python tools/generate_json_schemas.py
```

## Adding a New Fixture

To add a fixture and its contract test:

1. Create a Markdown file in `tests/fixtures/markdown/` that demonstrates the scenario you want to cover.
2. Run `python tools/update_expected_contracts.py` to generate the expected JSON output in `tests/fixtures/expected/`.
3. Create a contract test in `tests/contract/` that parses the fixture and asserts the properties that define the scenario. Focus on the properties specific to the scenario; asserting the full JSON blob makes tests brittle against unrelated changes.
4. Run `pytest tests/contract/` to confirm the new test passes.
