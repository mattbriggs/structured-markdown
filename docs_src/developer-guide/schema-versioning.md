# Schema Versioning

## Two Versioning Systems

The `structure_parser` package uses two distinct versioning systems that must not be confused. All Pydantic contract models (in `contracts/`) carry a `schema_version` field that defaults to `"1"` and identifies the shape of the parser's output contract — the fields, types, and semantics that downstream consumers depend on. All JSON Schema artifacts in `model/articles/` carry a semantic version string in a `version` field (currently `"0.1.0"`) that follows `MAJOR.MINOR.PATCH` conventions and tracks the authoring pattern language independently of the parser. Changes to one system do not automatically require changes to the other, but any change to either system that breaks a downstream consumer requires a version bump and migration notes in this document.

## Breaking Changes to Parser Contracts

A change to a Pydantic contract model is breaking when it forces downstream consumers to update their code. The following changes are always breaking:

- Removing or renaming a field on `ParsedDocument`, `ParseRunResult`, `ParseStats`, `StructuredContent`, `Unit`, `Component`, `Attribute`, `Diagnostic`, `Reference`, `ModelValidationResult`, `TransformReadiness`, or `TargetReadiness`
- Changing a field's type (for example, widening `str` to `str | list[str]` or narrowing `dict` to a typed model)
- Removing a diagnostic code from the SP-NNN series or changing the meaning of an existing code
- Changing the value of a `schema_version` field in a contract that downstream consumers read to gate processing

## Breaking Changes to Model Schemas

A change to a JSON Schema in `model/articles/` is breaking when it causes documents that previously passed validation to fail. The following changes are always breaking:

- Removing a field that appears under `required` in the schema
- Removing an enum value from `article_type`, `unit_type`, `component_type`, or `attribute_type`
- Adding a new `required` field without a default
- Tightening a constraint (for example, changing `minLength` from 0 to 1 on a field that may legitimately be empty)

## The Version Bump Protocol

When a breaking change is necessary, follow these steps in order:

1. Increment `schema_version` from `"1"` to `"2"` on every contract model directly affected. Do not increment unaffected models.
2. Run `python tools/generate_json_schemas.py` to regenerate the JSON Schema artifacts, then commit the output to a new `v2/` directory alongside `v1/`.
3. Add a dated migration note to this document describing what changed, what the old shape was, and how consumers should update their code.
4. Update the contract tests in `tests/contract/` to assert the new `schema_version` value and the new field shape.
5. Run `python tools/update_expected_contracts.py` to regenerate fixture baselines if the change affects classifier or enricher output, then confirm `pytest tests/contract/` passes.

## Non-Breaking Changes

The following changes can be made without bumping `schema_version`:

- Adding an optional field with a default value to any contract model
- Adding a new enum value to `ArticleType`, `UnitType`, `ComponentType`, `AttributeType`, `InformationType`, or `TriageStatus`
- Adding a new SP-NNN diagnostic code
- Adding a new readiness target to `TransformReadiness.targets`
- Adding a new validation profile in `validation/validation_profiles.py`
- Improving a diagnostic `message` or `remediation` string without changing its `code`

Non-breaking changes should be documented in the package changelog but do not require migration notes in this document.

## Generated Schemas in schemas/

The `schemas/` directory contains JSON Schema artifacts generated from the Pydantic models by `tools/generate_json_schemas.py`. These files are checked into version control so that downstream tools (IDEs, validators, code generators) can consume them without a Python dependency.

The directory structure mirrors the versioning:

```
schemas/
  parser/
    v1/
      ParsedDocument.schema.json
      ParseRunResult.schema.json
      Diagnostic.schema.json
      Reference.schema.json
  structured_markdown/
    v1/
      Article.schema.json
```

When `schema_version` on a contract increments to `"2"`, the corresponding generated schema moves to a `v2/` sibling directory. The `v1/` directory remains in place until all known consumers have migrated. To regenerate the current schemas after a non-breaking change:

```bash
python tools/generate_json_schemas.py
```

Commit the regenerated output alongside the Python change that caused it so the two stay in sync.
