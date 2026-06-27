"""Pipeline package for repository-scale Markdown processing."""
from __future__ import annotations

from structure_parser.contracts.pipeline import PipelineConfig, PipelineRunResult
from structure_parser.pipeline.orchestrator import PipelineOrchestrator


def run_pipeline(config: PipelineConfig) -> PipelineRunResult:
    """Run the parser pipeline over a content repository.

    :param config: Pipeline configuration.
    :returns: Aggregated pipeline run result.
    :side effects: Reads source files, writes parsed outputs and a CSV report.
    """
    return PipelineOrchestrator().run(config)


__all__ = ["PipelineOrchestrator", "run_pipeline"]
