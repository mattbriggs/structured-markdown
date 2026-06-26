# Writing Validators

## Validator Responsibility

A validator takes a serialized `StructuredContent` dictionary and checks it against a JSON Schema from the model directory, returning a `ModelValidationResult` that records whether the document is valid and any schema errors encountered. Validation is intentionally decoupled from parsing: the parser always produces a `ParsedDocument` even when validation fails, and the result is stored in `ParsedDocument.validation` as a nullable field. This design lets downstream consumers read and display partial results without blocking on schema compliance.

## The validate_against_schema Function

`validate_against_schema()` in `validation/schema_validator.py` is the primary entry point for programmatic validation:

```python
def validate_against_schema(
    data: dict[str, Any],
    schema_id: str,
    model_dir: Path | None = None,
    source_path: str | None = None,
) -> ModelValidationResult:
```

| Parameter | Type | Purpose |
|---|---|---|
| `data` | `dict[str, Any]` | The JSON-serializable dict to validate (typically `StructuredContent.model_dump()`) |
| `schema_id` | `str` | Filename of the target schema, e.g. `"artHowto.schema.json"` |
| `model_dir` | `Path \| None` | Override the default model directory; `None` uses `model/articles/` |
| `source_path` | `str \| None` | Path string attached to diagnostics for context |

The function loads the named schema from `model_dir`, builds a schema store, and validates `data` using `jsonschema.Draft7Validator`. It returns a `ModelValidationResult` with `valid=True` on success or a list of `Diagnostic` objects on failure. Individual schema violations are converted to SP-030 diagnostics, capped at 50 per run. Failures to locate the schema file produce an SP-031 diagnostic; unsupported schema versions produce SP-032.

## The Schema Store

Before validation runs, `_build_schema_store()` pre-loads every `.schema.json` file found recursively under the model directory. Each schema is registered under three keys:

1. Its absolute `file://` URI (e.g., `file:///…/articles/artHowto.schema.json`)
2. Its bare filename (e.g., `artHowto.schema.json`)
3. Its `$id` value when that value differs from the filename

Non-schema JSON files such as `compMapping.json` are also loaded by file URI. In addition, `_OFFLINE_STORE` pre-populates stub entries for Draft 7 and Draft 2019-09 meta-schemas so the resolver never issues a network request during validation. The full store is then passed to `jsonschema.RefResolver` as its `store` argument, keeping all `$ref` resolution local.

## Advisory vs. Strict Validation

The `validation_mode` field on `ParserConfig` controls how schema failures are surfaced. In `"advisory"` mode (the default), a validation failure appends SP-030 diagnostics to `ParsedDocument.diagnostics` with `severity=warning`. The document's `has_errors` property remains `False` unless other error-severity diagnostics exist, and downstream transforms can still proceed. In `"strict"` mode, a validation failure causes the parser to emit an SP-099 `internal_error` diagnostic with `severity=error`, setting `has_errors=True` and signaling to the caller that the document should not be forwarded for transformation. Strict mode is appropriate for CI pipelines that enforce schema compliance before publishing.

## The Known $ref Resolution Limitation

Cross-directory `$ref` resolution using `jsonschema.RefResolver` has a known limitation: when a nested schema uses a bare `$id` value (a relative string without a full URI) to identify itself, the resolver may anchor resolution to the wrong base directory when the referencing schema and the referenced schema live in different subdirectories. This causes `RefResolver` to fail silently or raise a `RefResolutionError`. The current implementation catches this exception in a broad `except` block and returns an advisory SP-030 warning rather than propagating the error. Documents affected by this limitation receive a warning message that reads "Schema resolution inconclusive." The schema store pre-loading mitigates most cases by registering all schemas by filename, but the limitation remains for complex multi-level cross-directory chains.

## Validation Profiles

`validation/validation_profiles.py` defines named `ValidationProfile` dataclasses that bundle a schema ID, a strictness flag, required metadata fields, and allowed article types:

| Profile | Schema | Strict | Required Metadata |
|---|---|---|---|
| `default` | `artArticle.schema.json` | No | — |
| `howto` | `artHowto.schema.json` | Yes | `title` |
| `concept` | `artConcept.schema.json` | Yes | `title` |
| `reference` | `artReference.schema.json` | Yes | `title` |

Call `get_profile(name)` to retrieve a profile; unknown names fall back to `"default"`. Profiles are used internally by the parser pipeline to select the correct schema based on the classified `article_type`. You can provide a custom `model_schema_dir` in `ParserConfig` to validate against schemas that are not part of the built-in model directory.

## Programmatic Validation with a Custom Schema Directory

To validate against your own schemas, pass a `model_schema_dir` in `ParserConfig`:

```python
from pathlib import Path
from structure_parser import parse_file
from structure_parser.contracts.config import ParserConfig

config = ParserConfig(
    model_schema_dir=Path("/my/schemas"),
    validation_mode="strict",
)
doc = parse_file("article.md", config=config)
if doc.validation and not doc.validation.valid:
    for diag in doc.validation.diagnostics:
        print(diag.code, diag.message)
```

You can also call `validate_against_schema()` directly without involving the parser, passing any JSON-serializable dict and any schema filename present in your custom directory.

## Interpreting ModelValidationResult

`ModelValidationResult` carries four fields relevant to consumers:

| Field | Type | Meaning |
|---|---|---|
| `valid` | `bool` | `True` if the document passed all schema checks |
| `schema_id` | `str \| None` | The schema filename used for validation |
| `diagnostics` | `list[Diagnostic]` | Schema violations as SP-030 entries; SP-031 for missing schema file; SP-032 for unsupported version |
| `source_path` | `str \| None` | The source file path attached for context |

Filter `diagnostics` by `code` to distinguish between structural violations (`SP-030`), missing schema files (`SP-031`), and unsupported schema versions (`SP-032`).

## Future Path: Migrating to the referencing Library

The `jsonschema` package deprecated `RefResolver` in version 4.18.0 in favor of the `referencing` library, which offers a cleaner URI resolution model and proper support for cross-directory `$ref` chains. The current implementation uses `RefResolver` because it integrates directly with `Draft7Validator`. A future migration should replace `_build_schema_store()` and the `RefResolver` construction with a `referencing.Registry` instance and pass it to `Draft7Validator` via the `registry` keyword argument introduced in jsonschema 4.18+. This change will resolve the cross-directory `$ref` limitation described above and eliminate the advisory catch-all for `RefResolutionError`.
