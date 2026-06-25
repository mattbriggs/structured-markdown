"""Schema.org transform-readiness evaluator."""
from __future__ import annotations

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.transform_readiness import TargetReadiness
from structure_parser.domain.enums import ReadinessStatus


class SchemaOrgReadinessEvaluator:
    """Evaluates whether a ParsedDocument is ready for Schema.org (JSON-LD) output."""

    target = "schema_org"

    def evaluate(self, doc: ParsedDocument) -> TargetReadiness:
        """Check Schema.org prerequisites for the given document.

        Prerequisites (required):
        - Title available for the ``schema:name`` property.

        Recommended (generates degraded rather than blocked):
        - ``description`` or ``ms.description`` metadata field.

        Args:
            doc: The parsed document to evaluate.

        Returns:
            A TargetReadiness with status ready or degraded (never blocked,
            because Schema.org output can always be attempted with partial data).
        """
        missing: list[str] = []
        met: list[str] = []

        if doc.title:
            met.append("Title available for name property")
        else:
            missing.append("Title required for schema:name")

        if doc.metadata.get("description") or doc.metadata.get("ms.description"):
            met.append("Description available")
        else:
            missing.append("description metadata field recommended")

        status = ReadinessStatus.ready if not missing else ReadinessStatus.degraded

        return TargetReadiness(
            target=self.target,
            status=status,
            prerequisites_met=met,
            prerequisites_missing=missing,
        )
