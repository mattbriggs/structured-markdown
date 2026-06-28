"""Markdown file discovery service for pipeline processing."""
from __future__ import annotations

import fnmatch
import logging
from pathlib import Path

from structure_parser.contracts.diagnostics import Diagnostic
from structure_parser.contracts.pipeline import (
    PIPE_001,
    PIPE_004,
    DiscoveredSource,
    PipelineConfig,
    make_pipeline_diagnostic,
)
from structure_parser.domain.enums import SourceFormat

_log = logging.getLogger("structure_parser.pipeline.discovery")

_MARKDOWN_SUFFIXES: frozenset[str] = frozenset({".md", ".markdown"})


class MarkdownDiscoveryService:
    """Recursively discovers Markdown files from PipelineConfig inputs."""

    def discover(
        self,
        config: PipelineConfig,
    ) -> tuple[list[DiscoveredSource], list[Diagnostic]]:
        """Discover all Markdown source files matching the pipeline configuration.

        :param config:
            Pipeline configuration with inputs and include/exclude patterns.
        :returns:
            Tuple of (discovered sources, pipeline diagnostics). Diagnostics use
            PIPE-001 for missing input paths and PIPE-004 for empty discovery results.
        :side effects:
            Logs discovery progress.
        """
        sources: list[DiscoveredSource] = []
        diags: list[Diagnostic] = []

        for input_path in config.inputs:
            if not input_path.exists():
                _log.warning("Input path does not exist: %s", input_path)
                diags.append(
                    make_pipeline_diagnostic(
                        PIPE_001,
                        f"Input path does not exist: {input_path}",
                        detail=str(input_path),
                    )
                )
                continue

            if input_path.is_file():
                self._add_file(input_path, input_path.parent, config, sources)
            else:
                self._scan_folder(input_path, config, sources)

        # Sort deterministically by (source_root, relative_path)
        sources.sort(key=lambda s: (str(s.source_root), s.relative_path.as_posix()))

        missing_paths = any(d.code == PIPE_001 for d in diags)
        if not sources and not missing_paths:
            _log.warning("No Markdown files discovered. Check include/exclude patterns.")
            diags.append(
                make_pipeline_diagnostic(
                    PIPE_004,
                    "No Markdown files were discovered.",
                )
            )

        _log.info(
            "pipeline.discovery.complete",
            extra={"discovered": len(sources), "diagnostics": len(diags)},
        )
        return sources, diags

    def _add_file(
        self,
        path: Path,
        source_root: Path,
        config: PipelineConfig,
        sources: list[DiscoveredSource],
    ) -> None:
        if not self._matches_include(path.name, config.include_patterns):
            return
        if self._matches_exclude(path.name, config.exclude_patterns):
            return
        relative = path.relative_to(source_root)
        sources.append(
            DiscoveredSource(
                source_root=source_root.resolve(),
                source_path=path.resolve(),
                relative_path=relative,
                source_format=SourceFormat.markdown,
            )
        )

    def _scan_folder(
        self,
        folder: Path,
        config: PipelineConfig,
        sources: list[DiscoveredSource],
    ) -> None:
        for candidate in sorted(folder.rglob("*")):
            if not candidate.is_file():
                continue
            if candidate.suffix not in _MARKDOWN_SUFFIXES:
                continue
            if not self._matches_include(candidate.name, config.include_patterns):
                continue
            relative = candidate.relative_to(folder)
            if self._matches_exclude(relative.as_posix(), config.exclude_patterns):
                continue
            sources.append(
                DiscoveredSource(
                    source_root=folder.resolve(),
                    source_path=candidate.resolve(),
                    relative_path=relative,
                    source_format=SourceFormat.markdown,
                )
            )

    @staticmethod
    def _matches_include(name: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatch(name, p) for p in patterns)

    @staticmethod
    def _matches_exclude(path_str: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatch(path_str, p) for p in patterns)
