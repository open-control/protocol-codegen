"""
Norm Type Decoder.

Handles decoding of normalized values (norm8, norm16).
Uses EncodingStrategy for protocol-specific byte layout and max values.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteReadOp,
    DecoderMethodSpec,
)
from protocol_codegen.generators.common.type_decoders.base import TypeDecoder


class NormDecoder(TypeDecoder):
    """Decoder for normalized types (norm8, norm16)."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("norm8", "norm16")

    def get_method_spec(self, type_name: str, description: str) -> DecoderMethodSpec:
        """Generate DecoderMethodSpec for norm decoding."""
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        norm_spec = self.strategy.get_norm_spec(type_name)
        if not norm_spec:
            raise ValueError(f"No norm spec for {type_name}")

        method_name = type_name[0].upper() + type_name[1:]

        if norm_spec.byte_count == 1:
            # Single byte norm
            mask = 0x7F if norm_spec.max_value == 127 else None
            byte_reads = (ByteReadOp(index=0, mask=mask),)
        else:
            # Multi-byte norm uses integer spec
            int_spec = norm_spec.integer_spec
            if not int_spec:
                raise ValueError(f"No integer spec for {type_name}")

            byte_reads = tuple(
                ByteReadOp(
                    index=i,
                    shift=shift,
                    mask=mask if mask != 0xFF else None,
                )
                for i, (shift, mask) in enumerate(
                    zip(int_spec.shifts, int_spec.masks, strict=True)
                )
            )

        return DecoderMethodSpec(
            type_name=type_name,
            method_name=method_name,
            result_type="float32",  # Norms decode to float
            byte_count=norm_spec.byte_count,
            byte_reads=byte_reads,
            doc_comment=f"{description} ({norm_spec.comment})",
            postamble=f"NORM_SCALE={norm_spec.max_value}",
        )
