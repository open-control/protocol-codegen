"""
Tests for file_utils module (incremental generation utilities).

Validates write_if_changed and GenerationStats behavior.
"""

from __future__ import annotations

from pathlib import Path

from protocol_codegen.core.file_utils import GenerationStats, write_if_changed


class TestWriteIfChanged:
    """Tests for write_if_changed function."""

    def test_write_new_file(self, tmp_path: Path) -> None:
        """New file should be written and return True."""
        target = tmp_path / "new_file.txt"
        content = "Hello, World!"

        result = write_if_changed(target, content)

        assert result is True
        assert target.exists()
        assert target.read_text() == content

    def test_skip_unchanged_file(self, tmp_path: Path) -> None:
        """Unchanged content should not be written, return False."""
        target = tmp_path / "existing.txt"
        content = "Same content"

        # Write initial content
        target.write_text(content)
        original_mtime = target.stat().st_mtime

        # Try to write same content
        result = write_if_changed(target, content)

        assert result is False
        # Verify mtime didn't change (file wasn't touched)
        assert target.stat().st_mtime == original_mtime

    def test_update_changed_file(self, tmp_path: Path) -> None:
        """Changed content should be written, return True."""
        target = tmp_path / "changed.txt"
        original_content = "Original"
        new_content = "Modified"

        # Write initial content
        target.write_text(original_content)

        # Write new content
        result = write_if_changed(target, new_content)

        assert result is True
        assert target.read_text() == new_content

    def test_create_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories should be created if they don't exist."""
        target = tmp_path / "deep" / "nested" / "path" / "file.txt"
        content = "Content"

        result = write_if_changed(target, content)

        assert result is True
        assert target.exists()
        assert target.read_text() == content

    def test_utf8_encoding(self, tmp_path: Path) -> None:
        """UTF-8 content should be handled correctly."""
        target = tmp_path / "unicode.txt"
        content = "Unicode: 你好世界 🌍"

        result = write_if_changed(target, content)

        assert result is True
        assert target.read_text(encoding="utf-8") == content

    def test_multiline_content(self, tmp_path: Path) -> None:
        """Multiline content should be compared correctly."""
        target = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3\n"

        # Write and verify unchanged
        write_if_changed(target, content)
        result = write_if_changed(target, content)

        assert result is False

    def test_whitespace_matters(self, tmp_path: Path) -> None:
        """Whitespace differences should trigger write."""
        target = tmp_path / "whitespace.txt"

        write_if_changed(target, "content")
        result = write_if_changed(target, "content ")  # Trailing space

        assert result is True
        assert target.read_text() == "content "


class TestGenerationStats:
    """Tests for GenerationStats class."""

    def test_empty_stats(self) -> None:
        """Empty stats should have zero counts."""
        stats = GenerationStats()

        assert stats.total == 0
        assert stats.written_count == 0
        assert stats.skipped_count == 0

    def test_record_write(self) -> None:
        """Recording a write should update written list."""
        stats = GenerationStats()
        stats.record_write(Path("file.txt"), was_written=True)

        assert stats.written_count == 1
        assert stats.skipped_count == 0
        assert stats.total == 1
        assert "file.txt" in stats.written

    def test_record_skip(self) -> None:
        """Recording a skip should update skipped list."""
        stats = GenerationStats()
        stats.record_write(Path("file.txt"), was_written=False)

        assert stats.written_count == 0
        assert stats.skipped_count == 1
        assert stats.total == 1
        assert "file.txt" in stats.skipped

    def test_mixed_results(self) -> None:
        """Mixed writes and skips should be counted correctly."""
        stats = GenerationStats()
        stats.record_write(Path("written1.txt"), was_written=True)
        stats.record_write(Path("written2.txt"), was_written=True)
        stats.record_write(Path("skipped1.txt"), was_written=False)

        assert stats.written_count == 2
        assert stats.skipped_count == 1
        assert stats.total == 3

    def test_summary_all_written(self) -> None:
        """Summary for all-written case."""
        stats = GenerationStats()
        stats.record_write(Path("a.txt"), True)
        stats.record_write(Path("b.txt"), True)

        summary = stats.summary()
        assert "2 files generated" in summary

    def test_summary_all_skipped(self) -> None:
        """Summary for all-skipped case."""
        stats = GenerationStats()
        stats.record_write(Path("a.txt"), False)
        stats.record_write(Path("b.txt"), False)

        summary = stats.summary()
        assert "2 files unchanged" in summary

    def test_summary_mixed(self) -> None:
        """Summary for mixed case."""
        stats = GenerationStats()
        stats.record_write(Path("written.txt"), True)
        stats.record_write(Path("skipped.txt"), False)

        summary = stats.summary()
        assert "1 files generated" in summary
        assert "1 unchanged" in summary

    def test_extracts_filename_only(self) -> None:
        """Should store only filename, not full path."""
        stats = GenerationStats()
        stats.record_write(Path("/long/path/to/file.txt"), True)

        assert stats.written == ["file.txt"]
