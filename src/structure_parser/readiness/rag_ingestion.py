"""RAG ingestion readiness evaluator."""
from __future__ import annotations

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.transform_readiness import TargetReadiness
from structure_parser.domain.enums import ReadinessStatus


class RagIngestionReadinessEvaluator:
    """Evaluates whether a ParsedDocument is ready for RAG (vector-store) ingestion."""

    target = "rag_ingestion"

    def evaluate(self, doc: ParsedDocument) -> TargetReadiness:
        """Check RAG ingestion prerequisites for the given document.

        Prerequisites:
        - Title improves chunk context (missing → degraded, not blocked).
        - Structured content with at least one unit (required for unit-level chunking).
        - No parse errors (parse errors may corrupt chunk quality).

        Args:
            doc: The parsed document to evaluate.

        Returns:
            A TargetReadiness with status ready / degraded / blocked.
        """
        missing: list[str] = []
        met: list[str] = []

        if doc.title:
            met.append("Document title available for chunk context")
        else:
            missing.append("Title improves RAG chunk context")

        if doc.structured_content and doc.structured_content.content:
            met.append("Document has structured units for chunking")
        else:
            missing.append("Structured content required for unit-level chunking")

        if not doc.has_errors:
            met.append("No parse errors")
        else:
            missing.append("Parse errors may affect chunk quality")

        if not missing:
            status = ReadinessStatus.ready
        elif met:
            status = ReadinessStatus.degraded
        else:
            status = ReadinessStatus.blocked

        return TargetReadiness(
            target=self.target,
            status=status,
            prerequisites_met=met,
            prerequisites_missing=missing,
        )
