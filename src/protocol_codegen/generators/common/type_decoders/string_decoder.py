"""
String Type Decoder.

Handles decoding of variable-length strings.
Uses EncodingStrategy for protocol-specific masks.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteReadOp,
    DecoderMethodSpec,
)
from protocol_codegen.generators.common.type_decoders.base import TypeDecoder


class StringDecoder(TypeDecoder):
    """Decoder for string type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("string",)

    def get_method_spec(self, type_name: str, description: str) -> DecoderMethodSpec:
        """Generate DecoderMethodSpec for string decoding."""
        if type_name != "string":
            raise ValueError(f"Unsupported type: {type_name}")

        string_spec = self.strategy.get_string_spec()

        return DecoderMethodSpec(
            type_name="string",
            method_name="String",
            result_type="string",
            byte_count=-1,  # Variable length
            byte_reads=(ByteReadOp(index=0),),  # Length byte
            doc_comment=f"{description} ({string_spec.comment})",
            postamble=f"LENGTH_MASK=0x{string_spec.length_mask:02X};CHAR_MASK=0x{string_spec.char_mask:02X};MAX_LENGTH={string_spec.max_length}",
        )
