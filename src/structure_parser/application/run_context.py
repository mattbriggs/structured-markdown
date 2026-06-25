"""Run context — shared state for one orchestrated parse run."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from structure_parser.contracts.config import ParserConfig
from structure_parser.contracts.diagnostics import Diagnostic


@dataclass
class RunContext:
    """Internal state for a single parse run. Not part of the public contract."""
    config: ParserConfig
    start_time: float = field(default_factory=time.monotonic)
    run_diagnostics: list[Diagnostic] = field(default_factory=list)

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.start_time) * 1000
