"""
Norm Type Encoder.

Handles encoding of norm8 and norm16 (normalized floats 0.0-1.0).
"""

from __future__ import annotations

from protocol_codegen.generators.core.encoding_ops import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.core.type_encoders.base import TypeEncoder


class NormEncoder(TypeEncoder):
    """Encoder for normalized float types."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("norm8", "norm16")

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate MethodSpec for norm encoding."""
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_norm_spec(type_name)
        if not spec:
            raise ValueError(f"No norm spec for {type_name}")

        max_val = spec.max_value
        method_name = type_name[0].upper() + type_name[1:]

        if spec.byte_count == 1:
            # Single byte norm
            byte_mask = 0x7F if max_val == 127 else 0xFF
            return MethodSpec(
                type_name=type_name,
                method_name=method_name,
                param_type=type_name,
                byte_count=1,
                byte_writes=(
                    ByteWriteOp(
                        index=0,
                        expression=f"norm & 0x{byte_mask:02X}",
                    ),
                ),
                doc_comment=f"{description} ({spec.comment})",
                preamble=f"NORM_CLAMP;NORM_SCALE={max_val}",
            )
        else:
            # Multi-byte norm uses integer spec
            int_spec = spec.integer_spec
            if not int_spec:
                raise ValueError(f"No integer spec for {type_name}")

            byte_writes = tuple(
                ByteWriteOp(
                    index=i,
                    expression=(
                        f"norm & 0x{mask:02X}"
                        if shift == 0
                        else f"(norm >> {shift}) & 0x{mask:02X}"
                    ),
                )
                for i, (shift, mask) in enumerate(
                    zip(int_spec.shifts, int_spec.masks, strict=True)
                )
            )

            return MethodSpec(
                type_name=type_name,
                method_name=method_name,
                param_type=type_name,
                byte_count=spec.byte_count,
                byte_writes=byte_writes,
                doc_comment=f"{description} ({spec.comment})",
                preamble=f"NORM_CLAMP;NORM_SCALE={max_val}",
            )
