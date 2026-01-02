"""
Encoding Strategy Pattern for protocol-specific size calculations and code generation.

This module defines the interface for encoding strategies used by
Serial8 (8-bit binary) and SysEx (7-bit MIDI-safe) protocols.

The strategy provides:
- Size calculations for payload estimation
- Encoding specifications for code generation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegerEncodingSpec:
    """Specification for encoding integer types.

    Describes how to split an integer into bytes with bit shifts and masks.

    Attributes:
        byte_count: Number of bytes in encoded form
        shifts: Bit shift for each byte (list of ints)
        masks: Mask for each byte (list of ints, e.g., 0xFF or 0x7F)
        comment: Description for code comments
    """

    byte_count: int
    shifts: tuple[int, ...]
    masks: tuple[int, ...]
    comment: str

    def __post_init__(self) -> None:
        """Validate that shifts and masks have correct length."""
        if len(self.shifts) != self.byte_count:
            raise ValueError(f"shifts must have {self.byte_count} elements")
        if len(self.masks) != self.byte_count:
            raise ValueError(f"masks must have {self.byte_count} elements")


@dataclass(frozen=True)
class NormEncodingSpec:
    """Specification for encoding normalized float types (norm8, norm16).

    Attributes:
        byte_count: Number of bytes in encoded form
        max_value: Maximum integer value (127 for 7-bit, 255 for 8-bit, 65535 for 16-bit)
        integer_spec: Optional IntegerEncodingSpec for multi-byte norms
        comment: Description for code comments
    """

    byte_count: int
    max_value: int
    integer_spec: IntegerEncodingSpec | None
    comment: str


@dataclass(frozen=True)
class StringEncodingSpec:
    """Specification for encoding string types.

    Attributes:
        length_mask: Mask for length byte (0xFF for 8-bit, 0x7F for 7-bit)
        char_mask: Mask for character bytes (0xFF or 0x7F)
        max_length: Maximum string length
        comment: Description for code comments
    """

    length_mask: int
    char_mask: int
    max_length: int
    comment: str


class EncodingStrategy(ABC):
    """Abstract base for protocol-specific encoding calculations and code generation."""

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

    # ─────────────────────────────────────────────────────────────────────────
    # Size Calculations (used by PayloadCalculator)
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────────────
    # Encoding Specifications (used by EncoderTemplate)
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_integer_spec(self, type_name: str) -> IntegerEncodingSpec | None:
        """Get encoding specification for integer types.

        Args:
            type_name: Type name (uint8, uint16, uint32, int8, int16, int32)

        Returns:
            IntegerEncodingSpec or None if not an integer type
        """
        ...

    @abstractmethod
    def get_norm_spec(self, type_name: str) -> NormEncodingSpec | None:
        """Get encoding specification for normalized float types.

        Args:
            type_name: Type name (norm8, norm16)

        Returns:
            NormEncodingSpec or None if not a norm type
        """
        ...

    @abstractmethod
    def get_string_spec(self) -> StringEncodingSpec:
        """Get encoding specification for string type."""
        ...

    @property
    @abstractmethod
    def bool_true_value(self) -> int:
        """Value to encode for True (typically 0x01)."""
        ...

    @property
    @abstractmethod
    def bool_false_value(self) -> int:
        """Value to encode for False (typically 0x00)."""
        ...

    @property
    @abstractmethod
    def include_message_name_default(self) -> bool:
        """Default value for include_message_name in struct generation."""
        ...
