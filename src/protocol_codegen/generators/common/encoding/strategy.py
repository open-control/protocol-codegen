"""
Encoding Strategy Pattern for protocol-specific size calculations.

This module defines the interface for encoding strategies used by
Serial8 (8-bit binary) and SysEx (7-bit MIDI-safe) protocols.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EncodingStrategy(ABC):
    """Abstract base for protocol-specific encoding calculations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Protocol name for documentation."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Encoding description for comments."""
        ...

    @abstractmethod
    def get_encoded_size(self, type_name: str, raw_size: int) -> int:
        """
        Get encoded size in bytes for a builtin type.

        Args:
            type_name: Builtin type name (e.g., 'bool', 'uint8', 'float32')
            raw_size: Raw size in bytes

        Returns:
            Encoded size in bytes
        """
        ...

    @abstractmethod
    def get_string_max_encoded_size(self, max_length: int) -> int:
        """Get max encoded size for a string field."""
        ...

    @abstractmethod
    def get_string_min_encoded_size(self) -> int:
        """Get min encoded size for a string (empty string)."""
        ...
