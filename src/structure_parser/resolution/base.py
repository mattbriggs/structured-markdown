"""Reference resolver protocol definition."""
from __future__ import annotations

from typing import Protocol

from structure_parser.contracts.references import Reference


class IReferenceResolver(Protocol):
    """Protocol satisfied by any reference resolver implementation."""

    def resolve(self, ref: Reference, base_path: str) -> Reference:
        """Attempt to resolve a reference.

        Args:
            ref: The reference to resolve.
            base_path: The absolute path of the document containing the reference,
                       used as the base for resolving relative hrefs.

        Returns:
            A new Reference with an updated state (resolved, unresolved, unsupported).
        """
        ...
