"""
Float Type Decoder.

Handles decoding of float32 using strategy-specific byte layout.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteReadOp,
    DecoderMethodSpec,
)
from protocol_codegen.generators.common.type_decoders.base import TypeDecoder


class FloatDecoder(TypeDecoder):
    """Decoder for float32 type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("float32",)

    def get_method_spec(self, type_name: str, description: str) -> DecoderMethodSpec:
        """Generate DecoderMethodSpec for float32 decoding."""
        if type_name != "float32":
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_integer_spec("float32")
        if not spec:
            raise ValueError("No float32 spec available")

        # Build byte read operations for bits
        byte_reads = tuple(
            ByteReadOp(
                index=i,
                shift=shift,
                mask=mask if mask != 0xFF else None,
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        return DecoderMethodSpec(
            type_name="float32",
            method_name="Float32",
            result_type="float32",
            byte_count=spec.byte_count,
            byte_reads=byte_reads,
            doc_comment=f"{description} ({spec.comment})",
            postamble="FLOAT_BITCAST",
        )
