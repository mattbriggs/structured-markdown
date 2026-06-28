"""Integration tests for pipeline dry-run behavior."""
import csv
from pathlib import Path

from structure_parser.application.commands import PipelineCommand
from structure_parser.contracts.pipeline import PipelineConfig

CONTENT_REPO = Path(__file__).parent.parent / "fixtures" / "content_repo"


class TestDryRun:
    def test_dry_run_does_not_write_json_files(self, tmp_path):
        config = PipelineConfig(
            inputs=[CONTENT_REPO],
            output_dir=tmp_path / "out",
            dry_run=True,
        )
        PipelineCommand().run(config)
        assert not (tmp_path / "out/index.md.json").exists()
        assert not (tmp_path / "out/guide/install.md.json").exists()
        assert not (tmp_path / "out/guide/configure.md.json").exists()
        assert not (tmp_path / "out/reference/api.md.json").exists()

    def test_dry_run_writes_csv_report(self, tmp_path):
        config = PipelineConfig(
            inputs=[CONTENT_REPO],
            output_dir=tmp_path / "out",
            dry_run=True,
        )
        PipelineCommand().run(config)
        assert (tmp_path / "out/pipeline-inventory.csv").exists()

    def test_dry_run_report_has_correct_row_count(self, tmp_path):
        config = PipelineConfig(
            inputs=[CONTENT_REPO],
            output_dir=tmp_path / "out",
            dry_run=True,
        )
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 4

    def test_dry_run_exits_0_for_clean_content(self, tmp_path):
        config = PipelineConfig(
            inputs=[CONTENT_REPO],
            output_dir=tmp_path / "out",
            dry_run=True,
        )
        _, code = PipelineCommand().run(config)
        assert code == 0

    def test_dry_run_target_paths_present_in_report(self, tmp_path):
        config = PipelineConfig(
            inputs=[CONTENT_REPO],
            output_dir=tmp_path / "out",
            dry_run=True,
        )
        PipelineCommand().run(config)
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Target paths are calculated even in dry-run mode
        for row in rows:
            assert row["target_path"].endswith(".json")
