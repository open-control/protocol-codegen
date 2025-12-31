"""Serial8 encoding strategy - direct 8-bit binary encoding."""

from __future__ import annotations

from .strategy import EncodingStrategy


class Serial8EncodingStrategy(EncodingStrategy):
    """8-bit binary encoding (no expansion)."""

    @property
    def name(self) -> str:
        return "Serial8"

    @property
    def description(self) -> str:
        return "8-bit binary"

    def get_encoded_size(self, type_name: str, raw_size: int) -> int:
        """Direct 8-bit sizes (no expansion)."""
        # bool, uint8, int8, norm8: 1 byte
        if type_name in ("bool", "uint8", "int8", "norm8"):
            return 1
        # uint16, int16, norm16: 2 bytes
        if type_name in ("uint16", "int16", "norm16"):
            return 2
        # uint32, int32, float32: 4 bytes
        if type_name in ("uint32", "int32", "float32"):
            return 4
        # Default: use raw size
        return raw_size

    def get_string_max_encoded_size(self, max_length: int) -> int:
        """String: 1 byte length prefix + chars."""
        return 1 + max_length

    def get_string_min_encoded_size(self) -> int:
        """Empty string: just length prefix."""
        return 1
