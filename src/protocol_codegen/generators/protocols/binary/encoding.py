"""Binary encoding strategy - direct 8-bit binary encoding."""

from __future__ import annotations

from protocol_codegen.generators.protocols.base import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)

# Pre-defined encoding specs for Binary (8-bit binary)
_SERIAL8_INTEGER_SPECS: dict[str, IntegerEncodingSpec] = {
    "uint8": IntegerEncodingSpec(
        byte_count=1,
        shifts=(0,),
        masks=(0xFF,),
        comment="1 byte, direct",
    ),
    "int8": IntegerEncodingSpec(
        byte_count=1,
        shifts=(0,),
        masks=(0xFF,),
        comment="1 byte, direct",
    ),
    "uint16": IntegerEncodingSpec(
        byte_count=2,
        shifts=(0, 8),
        masks=(0xFF, 0xFF),
        comment="2 bytes, little-endian",
    ),
    "int16": IntegerEncodingSpec(
        byte_count=2,
        shifts=(0, 8),
        masks=(0xFF, 0xFF),
        comment="2 bytes, little-endian",
    ),
    "uint32": IntegerEncodingSpec(
        byte_count=4,
        shifts=(0, 8, 16, 24),
        masks=(0xFF, 0xFF, 0xFF, 0xFF),
        comment="4 bytes, little-endian",
    ),
    "int32": IntegerEncodingSpec(
        byte_count=4,
        shifts=(0, 8, 16, 24),
        masks=(0xFF, 0xFF, 0xFF, 0xFF),
        comment="4 bytes, little-endian",
    ),
    "float32": IntegerEncodingSpec(
        byte_count=4,
        shifts=(0, 8, 16, 24),
        masks=(0xFF, 0xFF, 0xFF, 0xFF),
        comment="4 bytes, IEEE 754 little-endian",
    ),
}

_SERIAL8_NORM_SPECS: dict[str, NormEncodingSpec] = {
    "norm8": NormEncodingSpec(
        byte_count=1,
        max_value=255,
        integer_spec=None,
        comment="1 byte, full 8-bit range (0-255)",
    ),
    "norm16": NormEncodingSpec(
        byte_count=2,
        max_value=65535,
        integer_spec=_SERIAL8_INTEGER_SPECS["uint16"],
        comment="2 bytes, little-endian (0-65535)",
    ),
}

_SERIAL8_STRING_SPEC = StringEncodingSpec(
    length_mask=0xFF,
    char_mask=0xFF,
    max_length=255,
    comment="1 byte length prefix + data (max 255 chars)",
)


class BinaryEncodingStrategy(EncodingStrategy):
    """8-bit binary encoding (no expansion)."""

    @property
    def name(self) -> str:
        return "Binary"

    @property
    def description(self) -> str:
        return "8-bit binary"

    # ─────────────────────────────────────────────────────────────────────────
    # Size Calculations
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────────────
    # Encoding Specifications
    # ─────────────────────────────────────────────────────────────────────────

    def get_integer_spec(self, type_name: str) -> IntegerEncodingSpec | None:
        """Get 8-bit encoding spec for integer types."""
        return _SERIAL8_INTEGER_SPECS.get(type_name)

    def get_norm_spec(self, type_name: str) -> NormEncodingSpec | None:
        """Get 8-bit encoding spec for norm types."""
        return _SERIAL8_NORM_SPECS.get(type_name)

    def get_string_spec(self) -> StringEncodingSpec:
        """Get 8-bit encoding spec for strings."""
        return _SERIAL8_STRING_SPEC

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
        """Binary includes message name by default."""
        return True
