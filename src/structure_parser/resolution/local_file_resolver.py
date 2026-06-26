"""Local file reference resolver."""
from __future__ import annotations

from pathlib import Path

from structure_parser.contracts.references import Reference
from structure_parser.domain.enums import ResolutionState

# URL schemes that this resolver does not handle
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "ftps://")


class LocalFileResolver:
    """Resolves relative path references to files on the local filesystem.

    External URLs and anchor-only references are marked as unsupported rather
    than unresolved so that callers can distinguish "broken local link" from
    "this type of link is not checked here".
    """

    def resolve(self, ref: Reference, base_path: str) -> Reference:
        """Attempt to resolve a local file reference.

        Args:
            ref: The reference to resolve.
            base_path: Absolute path of the source document. Used as the base
                       directory when resolving relative hrefs.

        Returns:
            A new Reference whose ``state`` is one of:
            - ``resolved`` — the target file exists on disk.
            - ``unresolved`` — the path was resolved but the file is missing.
            - ``unsupported`` — the href is an external URL or anchor-only ref.
        """
        href = ref.href

        # External URLs and anchor-only refs are out of scope
        if href.startswith(_EXTERNAL_SCHEMES) or href.startswith("#"):
            return ref.model_copy(update={"state": ResolutionState.unsupported})

        # Separate path from fragment
        path_part, _sep, _fragment = href.partition("#")
        if not path_part:
            # Pure anchor reference — nothing to resolve on disk
            return ref.model_copy(update={"state": ResolutionState.unsupported})

        # Resolve relative to the source document directory
        base = Path(base_path)
        if not base.is_dir():  # treat files and non-existent paths alike
            base = base.parent

        target = (base / path_part).resolve()

        if target.exists():
            return ref.model_copy(
                update={
                    "state": ResolutionState.resolved,
                    "resolved_path": str(target),
                }
            )

        return ref.model_copy(update={"state": ResolutionState.unresolved})


def resolve_references(
    refs: list[Reference],
    base_path: str,
    resolver: LocalFileResolver | None = None,
) -> tuple[list[Reference], list[Reference]]:
    """Resolve a list of references using the local file resolver.

    Args:
        refs: References to process.
        base_path: Absolute path of the source document.
        resolver: Optional resolver instance; creates a default one if omitted.

    Returns:
        A ``(resolved_refs, unresolved_refs)`` tuple where *unresolved_refs*
        contains only those with state ``ResolutionState.unresolved``.
        References with state ``unsupported`` are placed in *resolved_refs*
        (they are not broken — they are simply not checked here).
    """
    r = resolver or LocalFileResolver()
    resolved: list[Reference] = []
    unresolved: list[Reference] = []

    for ref in refs:
        result = r.resolve(ref, base_path)
        if result.state == ResolutionState.unresolved:
            unresolved.append(result)
        else:
            resolved.append(result)

    return resolved, unresolved
