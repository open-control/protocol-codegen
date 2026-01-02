"""
Bool Type Decoder.

Handles decoding of boolean values.
"""

from __future__ import annotations

from protocol_codegen.generators.core.encoding_ops import (
    ByteReadOp,
    DecoderMethodSpec,
)
from protocol_codegen.generators.core.type_decoders.base import TypeDecoder


class BoolDecoder(TypeDecoder):
    """Decoder for boolean type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("bool",)

    def get_method_spec(self, type_name: str, description: str) -> DecoderMethodSpec:
        """Generate DecoderMethodSpec for bool decoding."""
        if type_name != "bool":
            raise ValueError(f"Unsupported type: {type_name}")

        return DecoderMethodSpec(
            type_name="bool",
            method_name="Bool",
            result_type="bool",
            byte_count=1,
            byte_reads=(ByteReadOp(index=0),),
            doc_comment=f"{description} (1 byte)",
        )
