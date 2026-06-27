"""Parsed document output writing and target path calculation."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from structure_parser.contracts.parsed_document import ParsedDocument
from structure_parser.contracts.pipeline import (
    PIPE_005,
    PIPE_006,
    PIPE_007,
    DiscoveredSource,
)

_log = logging.getLogger("structure_parser.pipeline.output")


class ParsedDocumentWriter:
    """Calculates target paths and serializes ParsedDocument results to JSON."""

    @staticmethod
    def target_for(source: DiscoveredSource, output_dir: Path) -> Path:
        """Calculate the target path for a discovered source.

        :param source: Discovered source file.
        :param output_dir: Pipeline output directory.
        :returns:
            Output path preserving the source relative path with ``.json`` appended,
            e.g. ``guide/install.md`` becomes ``<output_dir>/guide/install.md.json``.
        """
        return output_dir / source.relative_path.parent / (source.relative_path.name + ".json")

    def write(
        self,
        document: ParsedDocument,
        target_path: Path,
        dry_run: bool = False,
    ) -> str | None:
        """Serialize a ParsedDocument to the target path.

        :param document: ParsedDocument to serialize.
        :param target_path: Output file path.
        :param dry_run: When True, calculate the path but skip writing.
        :returns: ``PIPE-005`` error code string on write failure, ``None`` on success.
        :side effects: Creates parent directories and writes a UTF-8 JSON file.
        """
        if dry_run:
            _log.debug("Dry run: skipping write to %s", target_path)
            return None

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            data = document.model_dump(mode="json", by_alias=True)
            target_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            _log.debug("Wrote parsed output: %s", target_path)
            return None
        except OSError as exc:
            _log.error("Failed to write %s: %s", target_path, exc)
            return PIPE_005

    @staticmethod
    def check_overlap(inputs: list[Path], output_dir: Path) -> bool:
        """Check whether any input path and the output directory overlap unsafely.

        :param inputs: Source input paths (files or folders).
        :param output_dir: Pipeline output directory.
        :returns:
            ``True`` when the output directory is inside an input directory or vice versa.
        :side effects: Resolves paths to absolute form.
        """
        output_resolved = output_dir.resolve()
        for inp in inputs:
            if not inp.exists():
                continue
            inp_resolved = inp.resolve()
            try:
                output_resolved.relative_to(inp_resolved)
                _log.error("%s: %s", PIPE_006, f"output {output_dir} is inside input {inp}")
                return True
            except ValueError:
                pass
            try:
                inp_resolved.relative_to(output_resolved)
                _log.error("%s: %s", PIPE_006, f"input {inp} is inside output {output_dir}")
                return True
            except ValueError:
                pass
        return False

    @staticmethod
    def check_duplicate_targets(
        sources: list[DiscoveredSource],
        output_dir: Path,
    ) -> list[str]:
        """Detect sources that would produce the same target path.

        :param sources: List of discovered sources.
        :param output_dir: Pipeline output directory.
        :returns:
            List of relative path POSIX strings for sources with duplicate targets.
            Returns an empty list when there are no duplicates.
        :side effects: Logs PIPE-007 for each duplicate detected.
        """
        seen: dict[Path, str] = {}
        duplicates: list[str] = []
        for source in sources:
            target = ParsedDocumentWriter.target_for(source, output_dir)
            if target in seen:
                _log.error(
                    "%s: %s and %s both map to %s",
                    PIPE_007,
                    seen[target],
                    source.relative_path.as_posix(),
                    target,
                )
                duplicates.append(source.relative_path.as_posix())
            else:
                seen[target] = source.relative_path.as_posix()
        return duplicates
