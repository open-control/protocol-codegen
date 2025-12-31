"""SysEx encoding strategy - 7-bit MIDI-safe encoding."""

from __future__ import annotations

from .strategy import EncodingStrategy


class SysExEncodingStrategy(EncodingStrategy):
    """7-bit MIDI-safe encoding (with expansion)."""

    @property
    def name(self) -> str:
        return "SysEx"

    @property
    def description(self) -> str:
        return "7-bit MIDI-safe"

    def get_encoded_size(self, type_name: str, raw_size: int) -> int:
        """7-bit encoded sizes (with expansion)."""
        # bool: 1 byte (0x00 or 0x01)
        if type_name == "bool":
            return 1
        # uint8, int8, norm8: 1 byte (no encoding needed, values < 128)
        if type_name in ("uint8", "int8", "norm8"):
            return 1
        # uint16, int16, norm16: 2 -> 3 bytes (7-bit expansion)
        if type_name in ("uint16", "int16", "norm16"):
            return 3
        # uint32, int32, float32: 4 -> 5 bytes (7-bit expansion)
        if type_name in ("uint32", "int32", "float32"):
            return 5
        # Default: 7-bit encoding formula
        return ((raw_size * 8) + 6) // 7

    def get_string_max_encoded_size(self, max_length: int) -> int:
        """String: 1 byte length prefix + chars (all 7-bit safe)."""
        return 1 + max_length

    def get_string_min_encoded_size(self) -> int:
        """Empty string: just length prefix."""
        return 1
