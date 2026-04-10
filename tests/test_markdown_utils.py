"""Tests for markdown_utils module."""

import pytest
from pathlib import Path
from cap2obs.markdown_utils import parse_frontmatter, inject_properties, scan_markdown_index


class TestParseFrontmatter:
    def test_with_cap2obs_keys(self):
        """Test parsing existing cap2obs properties."""
        content = (
            '---\n'
            'title: My Note\n'
            'cap2obs_source: "note123"\n'
            'cap2obs_managed: true\n'
            'cap2obs_managed_date: 2026-01-01\n'
            '---\n'
            '# Heading\n'
        )
        result = parse_frontmatter(content)
        assert result["cap2obs_source"] == "note123"
        assert result["cap2obs_managed"] == "true"
        assert result["cap2obs_managed_date"] == "2026-01-01"

    def test_without_yaml(self):
        """Returns empty dict for files without frontmatter."""
        content = "# Just a heading\nNo frontmatter here."
        assert parse_frontmatter(content) == {}

    def test_partial_keys(self):
        """Returns only the keys that are present."""
        content = '---\ncap2obs_source: "stem"\n---\n# Body'
        result = parse_frontmatter(content)
        assert result["cap2obs_source"] == "stem"
        assert "cap2obs_managed" not in result
        assert "cap2obs_managed_date" not in result

    def test_empty_frontmatter_block(self):
        """Empty YAML block returns empty dict."""
        content = "---\n---\n# Body"
        assert parse_frontmatter(content) == {}

    def test_other_yaml_keys_ignored(self):
        """Non-cap2obs keys are not returned."""
        content = "---\ntitle: Test\ntags: [a, b]\n---\n# Body"
        result = parse_frontmatter(content)
        assert result == {}

    def test_unquoted_source_value(self):
        """Unquoted source values are parsed correctly."""
        content = "---\ncap2obs_source: plain_stem\n---\n# Body"
        result = parse_frontmatter(content)
        assert result["cap2obs_source"] == "plain_stem"

    def test_no_frontmatter_at_start(self):
        """Frontmatter not at start of file is not parsed."""
        content = "Some text\n---\ncap2obs_source: \"stem\"\n---\n"
        assert parse_frontmatter(content) == {}


class TestInjectProperties:
    def test_no_existing_yaml(self):
        """Creates frontmatter block when none exists."""
        content = "# My Note\nSome text."
        result = inject_properties(content, "stem123")
        assert result.startswith("---\n")
        assert 'cap2obs_source: "stem123"' in result
        assert "cap2obs_managed: false" in result
        assert "cap2obs_managed_date: " in result
        assert "# My Note" in result

    def test_with_existing_yaml_preserves_other_keys(self):
        """Appends cap2obs keys without removing other YAML content."""
        content = "---\ntitle: My Note\ntags: [a, b]\n---\n# Body"
        result = inject_properties(content, "stem123")
        assert "title: My Note" in result
        assert "tags: [a, b]" in result
        assert 'cap2obs_source: "stem123"' in result
        assert "cap2obs_managed: false" in result

    def test_updates_existing_cap2obs_keys(self):
        """Overwrites existing cap2obs_* keys with new values."""
        content = (
            '---\n'
            'cap2obs_source: "old_stem"\n'
            'cap2obs_managed: false\n'
            'cap2obs_managed_date:\n'
            '---\n'
            '# Body'
        )
        result = inject_properties(content, "new_stem", managed=True, managed_date="2026-01-01")
        assert 'cap2obs_source: "new_stem"' in result
        assert "cap2obs_managed: true" in result
        assert "cap2obs_managed_date: 2026-01-01" in result
        assert 'cap2obs_source: "old_stem"' not in result

    def test_managed_true_flag(self):
        """managed=True writes 'true' string."""
        content = "# Note"
        result = inject_properties(content, "stem", managed=True, managed_date="2026-01-15")
        assert "cap2obs_managed: true" in result
        assert "cap2obs_managed_date: 2026-01-15" in result

    def test_managed_false_flag(self):
        """managed=False writes 'false' string."""
        content = "# Note"
        result = inject_properties(content, "stem", managed=False)
        assert "cap2obs_managed: false" in result

    def test_body_content_preserved(self):
        """Body text after frontmatter is preserved unchanged."""
        content = "---\ntitle: T\n---\n# Body\n\nParagraph."
        result = inject_properties(content, "s")
        assert "# Body\n\nParagraph." in result

    def test_empty_file(self):
        """Works on completely empty content."""
        result = inject_properties("", "stem")
        assert 'cap2obs_source: "stem"' in result
        assert result.startswith("---\n")


class TestScanMarkdownIndex:
    def test_builds_correct_index(self, tmp_path):
        """Builds correct index from directory of .md files."""
        (tmp_path / "note.md").write_text(
            '---\ncap2obs_source: "note"\ncap2obs_managed: false\ncap2obs_managed_date:\n---\n# Note'
        )
        (tmp_path / "curated.md").write_text(
            '---\ncap2obs_source: "curated"\ncap2obs_managed: true\ncap2obs_managed_date: 2026-01-01\n---\n# Curated'
        )
        index = scan_markdown_index(tmp_path)
        assert "note" in index
        assert index["note"]["managed"] is False
        assert index["note"]["path"] == tmp_path / "note.md"
        assert "curated" in index
        assert index["curated"]["managed"] is True

    def test_excludes_files_without_source(self, tmp_path):
        """Files without cap2obs_source are not included."""
        (tmp_path / "legacy.md").write_text("# No frontmatter")
        index = scan_markdown_index(tmp_path)
        assert index == {}

    def test_nonexistent_directory(self, tmp_path):
        """Returns empty dict for non-existent directory."""
        result = scan_markdown_index(tmp_path / "nonexistent")
        assert result == {}

    def test_recursive_scan(self, tmp_path):
        """Scans subdirectories recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "note.md").write_text(
            '---\ncap2obs_source: "nested"\ncap2obs_managed: false\ncap2obs_managed_date:\n---\n# Nested'
        )
        index = scan_markdown_index(tmp_path)
        assert "nested" in index
        assert index["nested"]["path"] == subdir / "note.md"

    def test_empty_directory(self, tmp_path):
        """Empty directory returns empty dict."""
        assert scan_markdown_index(tmp_path) == {}
