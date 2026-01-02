"""
Integer Type Decoder.

Handles decoding of integer types: uint8, int8, uint16, int16, uint32, int32.
Uses EncodingStrategy to get protocol-specific byte layout.
"""

from __future__ import annotations

from protocol_codegen.generators.core.encoding_ops import (
    ByteReadOp,
    DecoderMethodSpec,
)
from protocol_codegen.generators.core.type_decoders.base import TypeDecoder


class IntegerDecoder(TypeDecoder):
    """Decoder for integer types."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("uint8", "int8", "uint16", "int16", "uint32", "int32")

    def get_method_spec(self, type_name: str, description: str) -> DecoderMethodSpec:
        """Generate DecoderMethodSpec for integer decoding."""
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_integer_spec(type_name)
        if not spec:
            raise ValueError(f"No integer spec for {type_name}")

        # Build byte read operations
        byte_reads = tuple(
            ByteReadOp(
                index=i,
                shift=shift,
                mask=mask if mask != 0xFF else None,
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        # Signed types need cast from unsigned
        needs_signed_cast = type_name.startswith("int") and spec.byte_count > 1

        # Method name: capitalize first letter of each word
        method_name = type_name[0].upper() + type_name[1:]

        return DecoderMethodSpec(
            type_name=type_name,
            method_name=method_name,
            result_type=type_name,
            byte_count=spec.byte_count,
            byte_reads=byte_reads,
            doc_comment=f"{description} ({spec.comment})",
            needs_signed_cast=needs_signed_cast,
        )
