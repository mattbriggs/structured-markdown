"""End-to-end pipeline integration tests using the content_repo fixture."""
import csv
import json
from pathlib import Path

from structure_parser.application.commands import PipelineCommand
from structure_parser.contracts.pipeline import PipelineConfig
from structure_parser.pipeline.orchestrator import PipelineOrchestrator

CONTENT_REPO = Path(__file__).parent.parent / "fixtures" / "content_repo"


class TestPipelineEndToEnd:
    def test_discovers_all_fixture_files(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        result = PipelineOrchestrator().run(config)
        assert result.stats.discovered_count == 4

    def test_all_files_parse_without_failures(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        result = PipelineOrchestrator().run(config)
        assert result.stats.failed_count == 0

    def test_json_output_files_written(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineOrchestrator().run(config)
        assert (tmp_path / "out/index.md.json").exists()
        assert (tmp_path / "out/guide/install.md.json").exists()
        assert (tmp_path / "out/guide/configure.md.json").exists()
        assert (tmp_path / "out/reference/api.md.json").exists()

    def test_json_output_is_valid_parsed_document(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineOrchestrator().run(config)
        data = json.loads((tmp_path / "out/index.md.json").read_text(encoding="utf-8"))
        assert "source_path" in data
        assert "schema_version" in data

    def test_relative_paths_preserved_in_output(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        result = PipelineOrchestrator().run(config)
        relative_paths = [f.source.relative_path.as_posix() for f in result.files]
        assert "index.md" in relative_paths
        assert "guide/install.md" in relative_paths
        assert "guide/configure.md" in relative_paths
        assert "reference/api.md" in relative_paths


class TestCsvReport:
    def test_report_written_to_default_location(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineCommand().run(config)
        assert (tmp_path / "out/pipeline-inventory.csv").exists()

    def test_report_has_one_row_per_file(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 4

    def test_report_rows_contain_required_columns(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert row["source_path"]
            assert row["relative_path"]
            assert row["target_path"]
            assert row["status"]
            assert row["run_id"]

    def test_all_statuses_are_parsed(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert row["status"] in ("parsed", "parsed_with_warnings", "failed", "skipped")


class TestExitCode:
    def test_exit_0_for_clean_content_repo(self, tmp_path):
        config = PipelineConfig(inputs=[CONTENT_REPO], output_dir=tmp_path / "out")
        _, code = PipelineCommand().run(config)
        assert code == 0
