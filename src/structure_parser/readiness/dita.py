"""DITA transform-readiness evaluator."""
from __future__ import annotations

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.transform_readiness import TargetReadiness
from structure_parser.domain.enums import ReadinessStatus


class DitaReadinessEvaluator:
    """Evaluates whether a ParsedDocument is ready for DITA output."""

    target = "dita"

    def evaluate(self, doc: ParsedDocument) -> TargetReadiness:
        """Check DITA prerequisites for the given document.

        Prerequisites:
        - Document must have an H1 title.
        - Article type must be classified (not "unknown").
        - DITA type mapping must be present.

        Args:
            doc: The parsed document to evaluate.

        Returns:
            A TargetReadiness with status ready / degraded / blocked.
        """
        missing: list[str] = []
        met: list[str] = []

        if doc.title:
            met.append("Document has a title")
        else:
            missing.append("Document must have an H1 title")

        sc = doc.structured_content
        if sc and sc.article_type.value != "unknown":
            met.append("Article type is classified")
        else:
            missing.append("Article type must be classified (not unknown)")

        if sc and sc.dita_type:
            met.append("DITA type is mapped")
        else:
            missing.append("DITA type mapping required")

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
