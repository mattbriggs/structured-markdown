"""Validation profiles — named sets of validation rules."""
from __future__ import annotations

from dataclasses import dataclass, field  # noqa: F401


@dataclass(frozen=True)
class ValidationProfile:
    name: str
    schema_id: str
    strict: bool = False
    required_metadata_fields: tuple[str, ...] = ()
    allowed_article_types: tuple[str, ...] = ()


PROFILES: dict[str, ValidationProfile] = {
    "default": ValidationProfile(
        name="default",
        schema_id="artArticle.schema.json",
        strict=False,
    ),
    "howto": ValidationProfile(
        name="howto",
        schema_id="artHowto.schema.json",
        strict=True,
        required_metadata_fields=("title",),
        allowed_article_types=("howto",),
    ),
    "concept": ValidationProfile(
        name="concept",
        schema_id="artConcept.schema.json",
        strict=True,
        required_metadata_fields=("title",),
        allowed_article_types=("concept",),
    ),
    "reference": ValidationProfile(
        name="reference",
        schema_id="artReference.schema.json",
        strict=True,
        required_metadata_fields=("title",),
        allowed_article_types=("reference",),
    ),
}


def get_profile(name: str) -> ValidationProfile:
    """Return the named profile, falling back to "default" if not found."""
    return PROFILES.get(name, PROFILES["default"])
