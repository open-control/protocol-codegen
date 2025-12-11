"""
File utilities for protocol code generation.

Provides utilities for incremental generation and file management.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def write_if_changed(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """
    Write content to file only if it differs from existing content.

    This enables incremental generation by avoiding unnecessary file writes,
    which:
    - Reduces disk I/O
    - Preserves file timestamps for unchanged files
    - Improves build system efficiency (unchanged files don't trigger rebuilds)

    Args:
        path: Target file path
        content: Content to write
        encoding: File encoding (default: utf-8)

    Returns:
        True if file was written (content changed or file didn't exist),
        False if file already had identical content.

    Example:
        >>> changed = write_if_changed(Path("Encoder.hpp"), generated_code)
        >>> if changed:
        ...     print("File updated")
        ... else:
        ...     print("File unchanged, skipped")
    """
    # Check if file exists and has same content
    if path.exists():
        try:
            existing_content = path.read_text(encoding=encoding)
            if existing_content == content:
                return False  # Content unchanged, skip write
        except (OSError, UnicodeDecodeError):
            pass  # If we can't read, just write

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write the new content
    path.write_text(content, encoding=encoding)
    return True


class GenerationStats:
    """
    Track statistics for incremental generation.

    Provides a summary of what was generated vs skipped.
    """

    def __init__(self) -> None:
        """Initialize empty stats."""
        self.written: list[str] = []
        self.skipped: list[str] = []

    def record_write(self, path: Path, was_written: bool) -> None:
        """
        Record a file generation result.

        Args:
            path: File path that was processed
            was_written: True if file was written, False if skipped
        """
        filename = path.name
        if was_written:
            self.written.append(filename)
        else:
            self.skipped.append(filename)

    @property
    def total(self) -> int:
        """Total number of files processed."""
        return len(self.written) + len(self.skipped)

    @property
    def written_count(self) -> int:
        """Number of files written (new or changed)."""
        return len(self.written)

    @property
    def skipped_count(self) -> int:
        """Number of files skipped (unchanged)."""
        return len(self.skipped)

    def summary(self) -> str:
        """
        Generate a summary string.

        Returns:
            Human-readable summary of generation results.
        """
        if self.skipped_count == 0:
            return f"{self.written_count} files generated"
        elif self.written_count == 0:
            return f"{self.skipped_count} files unchanged (all skipped)"
        else:
            return f"{self.written_count} files generated, {self.skipped_count} unchanged (skipped)"
