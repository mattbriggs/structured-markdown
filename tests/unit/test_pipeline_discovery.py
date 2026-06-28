"""Tests for MarkdownDiscoveryService."""
from structure_parser.contracts.pipeline import PIPE_001, PIPE_004, PipelineConfig
from structure_parser.pipeline.discovery import MarkdownDiscoveryService


def _make_config(tmp_path, inputs=None, include=None, exclude=None):
    return PipelineConfig(
        inputs=inputs or [tmp_path],
        output_dir=tmp_path / "out",
        include_patterns=include or ["*.md", "*.markdown"],
        exclude_patterns=exclude or [],
    )


class TestDiscoverNestedMarkdown:
    def test_discovers_flat_files(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        (tmp_path / "b.md").write_text("# B")
        config = _make_config(tmp_path)
        sources, diags = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 2
        assert diags == []

    def test_discovers_nested_files(self, tmp_path):
        (tmp_path / "guide").mkdir()
        (tmp_path / "guide/install.md").write_text("# Install")
        (tmp_path / "guide/configure.md").write_text("# Configure")
        (tmp_path / "index.md").write_text("# Index")
        config = _make_config(tmp_path)
        sources, diags = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 3
        assert diags == []

    def test_ignores_non_markdown_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Readme")
        (tmp_path / "data.json").write_text("{}")
        (tmp_path / "script.py").write_text("pass")
        config = _make_config(tmp_path)
        sources, _ = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 1

    def test_discovers_dot_markdown_extension(self, tmp_path):
        (tmp_path / "readme.markdown").write_text("# Readme")
        config = _make_config(tmp_path)
        sources, _ = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 1
        assert sources[0].relative_path.name == "readme.markdown"


class TestDeterministicOrdering:
    def test_sorted_by_relative_path(self, tmp_path):
        (tmp_path / "guide").mkdir()
        (tmp_path / "guide/z.md").write_text("# Z")
        (tmp_path / "guide/a.md").write_text("# A")
        (tmp_path / "index.md").write_text("# Index")
        config = _make_config(tmp_path)
        sources, _ = MarkdownDiscoveryService().discover(config)
        paths = [s.relative_path.as_posix() for s in sources]
        assert paths == sorted(paths)


class TestIncludeExcludePatterns:
    def test_exclude_file_pattern(self, tmp_path):
        (tmp_path / "index.md").write_text("# Index")
        (tmp_path / "draft.md").write_text("# Draft")
        config = _make_config(tmp_path, exclude=["draft.md"])
        sources, _ = MarkdownDiscoveryService().discover(config)
        names = [s.relative_path.name for s in sources]
        assert "draft.md" not in names
        assert "index.md" in names

    def test_exclude_folder_pattern(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "site").mkdir()
        (tmp_path / "docs/index.md").write_text("# Docs")
        (tmp_path / "site/index.md").write_text("# Site")
        config = _make_config(tmp_path, exclude=["site/*"])
        sources, _ = MarkdownDiscoveryService().discover(config)
        paths = [s.relative_path.as_posix() for s in sources]
        assert all("site/" not in p for p in paths)
        assert any("docs/" in p for p in paths)

    def test_include_pattern_filters(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Readme")
        (tmp_path / "notes.txt.md").write_text("# Notes")
        config = _make_config(tmp_path, include=["readme.md"])
        sources, _ = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 1
        assert sources[0].relative_path.name == "readme.md"


class TestMissingInputPath:
    def test_missing_path_emits_pipe_001(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        config = _make_config(tmp_path, inputs=[missing])
        sources, diags = MarkdownDiscoveryService().discover(config)
        assert sources == []
        assert any(d.code == PIPE_001 for d in diags)

    def test_no_files_emits_pipe_004(self, tmp_path):
        config = _make_config(tmp_path)
        sources, diags = MarkdownDiscoveryService().discover(config)
        assert sources == []
        assert any(d.code == PIPE_004 for d in diags)

    def test_missing_path_does_not_emit_pipe_004(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        config = _make_config(tmp_path, inputs=[missing])
        _, diags = MarkdownDiscoveryService().discover(config)
        codes = [d.code for d in diags]
        assert PIPE_001 in codes
        assert PIPE_004 not in codes


class TestExplicitFileInput:
    def test_single_file_input(self, tmp_path):
        f = tmp_path / "readme.md"
        f.write_text("# Readme")
        config = _make_config(tmp_path, inputs=[f])
        sources, diags = MarkdownDiscoveryService().discover(config)
        assert len(sources) == 1
        assert diags == []
        assert sources[0].source_path == f.resolve()

    def test_resolved_paths_stored(self, tmp_path):
        f = tmp_path / "readme.md"
        f.write_text("# Readme")
        config = _make_config(tmp_path, inputs=[f])
        sources, _ = MarkdownDiscoveryService().discover(config)
        assert sources[0].source_path.is_absolute()
