"""SysEx encoding strategy - 7-bit MIDI-safe encoding."""

from __future__ import annotations

from .strategy import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)

# Pre-defined encoding specs for SysEx (7-bit MIDI-safe)
_SYSEX_INTEGER_SPECS: dict[str, IntegerEncodingSpec] = {
    "uint8": IntegerEncodingSpec(
        byte_count=1,
        shifts=(0,),
        masks=(0x7F,),
        comment="1 byte, 7-bit masked",
    ),
    "int8": IntegerEncodingSpec(
        byte_count=1,
        shifts=(0,),
        masks=(0x7F,),
        comment="1 byte, 7-bit masked",
    ),
    "uint16": IntegerEncodingSpec(
        byte_count=3,
        shifts=(0, 7, 14),
        masks=(0x7F, 0x7F, 0x03),
        comment="2 bytes → 3 bytes, 7-bit encoding",
    ),
    "int16": IntegerEncodingSpec(
        byte_count=3,
        shifts=(0, 7, 14),
        masks=(0x7F, 0x7F, 0x03),
        comment="2 bytes → 3 bytes, 7-bit encoding",
    ),
    "uint32": IntegerEncodingSpec(
        byte_count=5,
        shifts=(0, 7, 14, 21, 28),
        masks=(0x7F, 0x7F, 0x7F, 0x7F, 0x0F),
        comment="4 bytes → 5 bytes, 7-bit encoding",
    ),
    "int32": IntegerEncodingSpec(
        byte_count=5,
        shifts=(0, 7, 14, 21, 28),
        masks=(0x7F, 0x7F, 0x7F, 0x7F, 0x0F),
        comment="4 bytes → 5 bytes, 7-bit encoding",
    ),
    "float32": IntegerEncodingSpec(
        byte_count=5,
        shifts=(0, 7, 14, 21, 28),
        masks=(0x7F, 0x7F, 0x7F, 0x7F, 0x0F),
        comment="4 bytes → 5 bytes, 7-bit encoding (IEEE 754)",
    ),
}

_SYSEX_NORM_SPECS: dict[str, NormEncodingSpec] = {
    "norm8": NormEncodingSpec(
        byte_count=1,
        max_value=127,
        integer_spec=None,
        comment="1 byte, 7-bit range (0-127)",
    ),
    "norm16": NormEncodingSpec(
        byte_count=3,
        max_value=65535,
        integer_spec=_SYSEX_INTEGER_SPECS["uint16"],
        comment="2 bytes → 3 bytes, 7-bit encoding (0-65535)",
    ),
}

_SYSEX_STRING_SPEC = StringEncodingSpec(
    length_mask=0x7F,
    char_mask=0x7F,
    max_length=127,
    comment="1 byte length prefix + data (max 127 chars, 7-bit safe)",
)


class SysExEncodingStrategy(EncodingStrategy):
    """7-bit MIDI-safe encoding (with expansion)."""

    @property
    def name(self) -> str:
        return "SysEx"

    @property
    def description(self) -> str:
        return "7-bit MIDI-safe"

    # ─────────────────────────────────────────────────────────────────────────
    # Size Calculations
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────────────
    # Encoding Specifications
    # ─────────────────────────────────────────────────────────────────────────

    def get_integer_spec(self, type_name: str) -> IntegerEncodingSpec | None:
        """Get 7-bit encoding spec for integer types."""
        return _SYSEX_INTEGER_SPECS.get(type_name)

    def get_norm_spec(self, type_name: str) -> NormEncodingSpec | None:
        """Get 7-bit encoding spec for norm types."""
        return _SYSEX_NORM_SPECS.get(type_name)

    def get_string_spec(self) -> StringEncodingSpec:
        """Get 7-bit encoding spec for strings."""
        return _SYSEX_STRING_SPEC

    @property
    def bool_true_value(self) -> int:
        """True = 0x01."""
        return 0x01

    @property
    def bool_false_value(self) -> int:
        """False = 0x00."""
        return 0x00

    @property
    def include_message_name_default(self) -> bool:
        """SysEx does not include message name by default."""
        return False
