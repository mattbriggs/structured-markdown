"""Transform-readiness evaluator protocol and runner."""
from __future__ import annotations

from typing import Protocol

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.transform_readiness import TargetReadiness, TransformReadiness


class IReadinessEvaluator(Protocol):
    """Protocol satisfied by any single-target readiness evaluator."""

    target: str

    def evaluate(self, doc: ParsedDocument) -> TargetReadiness:
        """Evaluate readiness for this target.

        No transform is executed; this only checks whether the document meets
        the prerequisites for the given output target.

        Args:
            doc: The parsed document to evaluate.

        Returns:
            A TargetReadiness with a status and lists of met/missing prerequisites.
        """
        ...


def evaluate_readiness(
    doc: ParsedDocument,
    evaluators: list[IReadinessEvaluator],
) -> TransformReadiness:
    """Run all evaluators against a ParsedDocument and aggregate the results.

    Args:
        doc: The parsed document to evaluate.
        evaluators: A list of evaluator objects, one per output target.

    Returns:
        A TransformReadiness aggregating all per-target results.
    """
    targets = [e.evaluate(doc) for e in evaluators]
    return TransformReadiness(source_path=doc.source_path, targets=targets)
