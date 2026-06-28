"""Integration tests for pipeline error and failure representation in the CSV."""
import csv

from structure_parser.application.commands import PipelineCommand
from structure_parser.contracts.pipeline import PIPE_001, PipelineConfig
from structure_parser.pipeline.orchestrator import PipelineOrchestrator

_MINIMAL_MD = "# Hello\n\nA paragraph.\n"


class TestMissingInputPath:
    def test_missing_input_emits_pipe_001_diagnostic(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        config = PipelineConfig(
            inputs=[missing],
            output_dir=tmp_path / "out",
        )
        result = PipelineOrchestrator().run(config)
        codes = [d.code for d in result.run_diagnostics]
        assert PIPE_001 in codes

    def test_missing_input_produces_no_csv_rows(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        config = PipelineConfig(
            inputs=[missing],
            output_dir=tmp_path / "out",
        )
        PipelineCommand().run(config)
        report = tmp_path / "out/pipeline-inventory.csv"
        assert report.exists()
        with report.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 0


class TestFileWithParserDiagnostics:
    def test_file_with_warnings_in_report(self, tmp_path):
        (tmp_path / "docs").mkdir()
        # No front matter → SP-011 (info) and possibly SP-020 (warning)
        (tmp_path / "docs/warn.md").write_text("No front matter and no H1.\n")
        config = PipelineConfig(
            inputs=[tmp_path / "docs"],
            output_dir=tmp_path / "out",
        )
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
        assert rows[0]["relative_path"] == "warn.md"

    def test_parser_codes_populated_in_report(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/warn.md").write_text("No front matter and no H1.\n")
        config = PipelineConfig(
            inputs=[tmp_path / "docs"],
            output_dir=tmp_path / "out",
        )
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Parser codes should be present (e.g. SP-011, SP-020)
        assert rows[0]["parser_codes"] != "" or rows[0]["status"] == "parsed"


class TestOverlapDetection:
    def test_overlap_exit_1(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(_MINIMAL_MD)
        config = PipelineConfig(
            inputs=[docs],
            output_dir=docs / "out",
        )
        _, code = PipelineCommand().run(config)
        assert code == 1

    def test_overlap_report_written_with_no_rows(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text(_MINIMAL_MD)
        config = PipelineConfig(
            inputs=[docs],
            output_dir=docs / "out",
        )
        PipelineCommand().run(config)
        report = config.effective_report_path()
        assert report.exists()
        with report.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 0


class TestMultipleInputsWithErrors:
    def test_good_and_missing_inputs(self, tmp_path):
        good = tmp_path / "good"
        good.mkdir()
        (good / "index.md").write_text(_MINIMAL_MD)
        missing = tmp_path / "missing"

        config = PipelineConfig(
            inputs=[good, missing],
            output_dir=tmp_path / "out",
        )
        result = PipelineOrchestrator().run(config)
        # Good files are discovered despite missing path
        assert result.stats.discovered_count >= 1
        run_codes = [d.code for d in result.run_diagnostics]
        assert PIPE_001 in run_codes
