"""Tests for CsvInventoryReporter."""
import csv
from pathlib import Path

from structure_parser.contracts.pipeline import (
    DiscoveredSource,
    PipelineFileResult,
    PipelineFileStatus,
    PipelineRunResult,
    PipelineRunStats,
)
from structure_parser.pipeline.reporting import CSV_FIELDS, CsvInventoryReporter


def _make_source(root: Path, relative: str = "index.md") -> DiscoveredSource:
    return DiscoveredSource(
        source_root=root,
        source_path=root / relative,
        relative_path=Path(relative),
    )


def _make_result(run_id: str = "abc", files: list | None = None) -> PipelineRunResult:
    return PipelineRunResult(run_id=run_id, files=files or [], stats=PipelineRunStats())


class TestCsvHeaders:
    def test_writes_all_expected_headers(self, tmp_path):
        reporter = CsvInventoryReporter()
        report_path = tmp_path / "report.csv"
        reporter.write(_make_result(), report_path)

        with report_path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == CSV_FIELDS

    def test_header_present_for_empty_result(self, tmp_path):
        reporter = CsvInventoryReporter()
        report_path = tmp_path / "report.csv"
        reporter.write(_make_result(), report_path)
        lines = report_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1  # header only
        assert "run_id" in lines[0]


class TestCsvRows:
    def test_one_row_per_file(self, tmp_path):
        root = tmp_path / "docs"
        files = [
            PipelineFileResult(
                source=_make_source(root, "a.md"),
                target_path=tmp_path / "out" / "a.md.json",
                status=PipelineFileStatus.parsed,
            ),
            PipelineFileResult(
                source=_make_source(root, "b.md"),
                target_path=tmp_path / "out" / "b.md.json",
                status=PipelineFileStatus.parsed,
            ),
        ]
        result = _make_result(files=files)
        reporter = CsvInventoryReporter()
        report_path = tmp_path / "report.csv"
        reporter.write(result, report_path)

        with report_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2

    def test_run_id_in_each_row(self, tmp_path):
        root = tmp_path / "docs"
        files = [
            PipelineFileResult(
                source=_make_source(root),
                status=PipelineFileStatus.parsed,
            )
        ]
        result = _make_result(run_id="myrunid", files=files)
        report_path = tmp_path / "report.csv"
        CsvInventoryReporter().write(result, report_path)
        with report_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["run_id"] == "myrunid"

    def test_parser_codes_semicolon_delimited(self, tmp_path):
        root = tmp_path / "docs"
        files = [
            PipelineFileResult(
                source=_make_source(root),
                status=PipelineFileStatus.parsed_with_warnings,
                parser_codes=["SP-011", "SP-020", "SP-041"],
            )
        ]
        result = _make_result(files=files)
        report_path = tmp_path / "report.csv"
        CsvInventoryReporter().write(result, report_path)
        with report_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["parser_codes"] == "SP-011;SP-020;SP-041"

    def test_failed_status_in_row(self, tmp_path):
        root = tmp_path / "docs"
        files = [
            PipelineFileResult(
                source=_make_source(root),
                status=PipelineFileStatus.failed,
                pipeline_code="PIPE-005",
                error_count=1,
            )
        ]
        result = _make_result(files=files)
        report_path = tmp_path / "report.csv"
        CsvInventoryReporter().write(result, report_path)
        with report_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["status"] == "failed"
        assert rows[0]["pipeline_code"] == "PIPE-005"
        assert rows[0]["error_count"] == "1"

    def test_empty_pipeline_code_for_success(self, tmp_path):
        root = tmp_path / "docs"
        files = [
            PipelineFileResult(
                source=_make_source(root),
                status=PipelineFileStatus.parsed,
            )
        ]
        result = _make_result(files=files)
        report_path = tmp_path / "report.csv"
        CsvInventoryReporter().write(result, report_path)
        with report_path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["pipeline_code"] == ""


class TestReportPathHandling:
    def test_creates_parent_directories(self, tmp_path):
        report_path = tmp_path / "nested" / "deeply" / "report.csv"
        CsvInventoryReporter().write(_make_result(), report_path)
        assert report_path.exists()

    def test_returns_pipe_003_on_failure(self, tmp_path):
        bad_path = tmp_path / "report.csv"
        bad_path.mkdir()  # directory instead of file
        error = CsvInventoryReporter().write(_make_result(), bad_path)
        assert error == "PIPE-003"

    def test_returns_none_on_success(self, tmp_path):
        report_path = tmp_path / "report.csv"
        error = CsvInventoryReporter().write(_make_result(), report_path)
        assert error is None
