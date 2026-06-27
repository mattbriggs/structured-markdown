"""CSV inventory reporter for pipeline runs."""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from structure_parser.contracts.pipeline import PIPE_003, PipelineRunResult

_log = logging.getLogger("structure_parser.pipeline.reporting")

CSV_FIELDS = [
    "run_id",
    "source_root",
    "source_path",
    "relative_path",
    "target_path",
    "status",
    "parser_codes",
    "pipeline_code",
    "error_count",
    "warning_count",
    "duration_ms",
]


class CsvInventoryReporter:
    """Writes a CSV inventory report from a completed PipelineRunResult."""

    def write(self, result: PipelineRunResult, report_path: Path) -> str | None:
        """Write the CSV inventory report for a completed pipeline run.

        :param result: Completed pipeline run result.
        :param report_path: Output CSV path.
        :returns: ``PIPE-003`` error code string on write failure, ``None`` on success.
        :side effects: Creates parent directories and writes a UTF-8 CSV file.
        """
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
                writer.writeheader()
                for file_result in result.files:
                    writer.writerow(
                        {
                            "run_id": result.run_id,
                            "source_root": file_result.source.source_root.as_posix(),
                            "source_path": file_result.source.source_path.as_posix(),
                            "relative_path": file_result.source.relative_path.as_posix(),
                            "target_path": (
                                file_result.target_path.as_posix()
                                if file_result.target_path
                                else ""
                            ),
                            "status": file_result.status,
                            "parser_codes": ";".join(file_result.parser_codes),
                            "pipeline_code": file_result.pipeline_code or "",
                            "error_count": file_result.error_count,
                            "warning_count": file_result.warning_count,
                            "duration_ms": f"{file_result.duration_ms:.1f}",
                        }
                    )
            _log.info(
                "pipeline.report.written",
                extra={"report_path": str(report_path), "rows": len(result.files)},
            )
            return None
        except OSError as exc:
            _log.error("Failed to write report %s: %s", report_path, exc)
            return PIPE_003
