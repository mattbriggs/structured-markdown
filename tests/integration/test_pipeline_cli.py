"""Integration tests for the `structure-parser pipe` CLI command."""
import csv
from pathlib import Path

from typer.testing import CliRunner

from structure_parser.cli import app

CONTENT_REPO = Path(__file__).parent.parent / "fixtures" / "content_repo"
runner = CliRunner()


class TestPipeCommand:
    def test_pipe_exits_0_for_clean_content(self, tmp_path):
        result = runner.invoke(
            app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")]
        )
        assert result.exit_code == 0

    def test_pipe_writes_json_files(self, tmp_path):
        runner.invoke(app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")])
        assert (tmp_path / "out/index.md.json").exists()
        assert (tmp_path / "out/guide/install.md.json").exists()
        assert (tmp_path / "out/guide/configure.md.json").exists()
        assert (tmp_path / "out/reference/api.md.json").exists()

    def test_pipe_writes_default_csv_report(self, tmp_path):
        runner.invoke(app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")])
        assert (tmp_path / "out/pipeline-inventory.csv").exists()

    def test_pipe_summary_output_shown(self, tmp_path):
        result = runner.invoke(
            app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")]
        )
        assert "Pipeline parsed" in result.output

    def test_pipe_custom_report_path(self, tmp_path):
        custom_report = tmp_path / "custom_report.csv"
        runner.invoke(
            app,
            [
                "pipe",
                str(CONTENT_REPO),
                "--out",
                str(tmp_path / "out"),
                "--report",
                str(custom_report),
            ],
        )
        assert custom_report.exists()

    def test_pipe_dry_run_flag(self, tmp_path):
        runner.invoke(
            app,
            ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out"), "--dry-run"],
        )
        assert not (tmp_path / "out/index.md.json").exists()
        assert (tmp_path / "out/pipeline-inventory.csv").exists()

    def test_pipe_exclude_pattern(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "pipe",
                str(CONTENT_REPO),
                "--out",
                str(tmp_path / "out"),
                "--exclude",
                "guide/*",
            ],
        )
        assert result.exit_code == 0
        assert not (tmp_path / "out/guide/install.md.json").exists()
        assert (tmp_path / "out/index.md.json").exists()

    def test_pipe_report_has_correct_row_count(self, tmp_path):
        runner.invoke(app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")])
        with (tmp_path / "out/pipeline-inventory.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 4

    def test_pipe_missing_out_option_exits_nonzero(self, tmp_path):
        result = runner.invoke(app, ["pipe", str(CONTENT_REPO)])
        assert result.exit_code != 0


class TestPipeCommandWithLogFile:
    def test_log_file_created_when_requested(self, tmp_path):
        log_path = tmp_path / "pipeline.log"
        runner.invoke(
            app,
            [
                "pipe",
                str(CONTENT_REPO),
                "--out",
                str(tmp_path / "out"),
                "--log-file",
                str(log_path),
            ],
        )
        assert log_path.exists()
        assert log_path.stat().st_size > 0

    def test_no_log_file_by_default(self, tmp_path):
        runner.invoke(app, ["pipe", str(CONTENT_REPO), "--out", str(tmp_path / "out")])
        # No log file created unless explicitly requested
        log_candidates = list((tmp_path / "out").glob("*.log"))
        assert log_candidates == []
