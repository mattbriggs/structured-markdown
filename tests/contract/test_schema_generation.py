"""Contract test: schema repository loads schemas correctly."""

import pytest

from structure_parser.domain.errors import SchemaRepositoryError
from structure_parser.repositories.schema_repository import (
    get_default_model_dir,
    list_schemas,
    load_schema,
)


class TestSchemaRepository:
    def test_default_model_dir_exists(self):
        model_dir = get_default_model_dir()
        assert model_dir.exists()

    def test_list_schemas_non_empty(self):
        schemas = list_schemas()
        assert len(schemas) > 0

    def test_load_article_schema(self):
        schema = load_schema("artArticle.schema.json")
        assert "$schema" in schema or "oneOf" in schema

    def test_load_shared_article_schema(self):
        schema = load_schema("sharedArticle.schema.json")
        assert "$defs" in schema

    def test_load_missing_schema_raises(self):
        with pytest.raises(SchemaRepositoryError):
            load_schema("nonexistent.schema.json")

    def test_all_article_schemas_loadable(self):
        schemas = list_schemas()
        article_schemas = [s for s in schemas if s.startswith("art") and s.endswith(".schema.json")]
        for schema_id in article_schemas:
            schema = load_schema(schema_id)
            assert isinstance(schema, dict)
