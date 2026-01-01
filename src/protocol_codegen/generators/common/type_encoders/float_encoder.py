"""
Float Type Encoder.

Handles encoding of float32 using bitcast to uint32 then integer encoding.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.type_encoders.base import TypeEncoder


class FloatEncoder(TypeEncoder):
    """Encoder for float32 type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("float32",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate MethodSpec for float32 encoding."""
        if type_name != "float32":
            raise ValueError(f"Unsupported type: {type_name}")

        # Float uses same encoding as uint32 after bitcast
        spec = self.strategy.get_integer_spec("float32")
        if not spec:
            raise ValueError("No float32 spec in strategy")

        byte_writes = tuple(
            ByteWriteOp(
                index=i,
                expression=(
                    f"bits & 0x{mask:02X}"
                    if shift == 0
                    else f"(bits >> {shift}) & 0x{mask:02X}"
                ),
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        return MethodSpec(
            type_name="float32",
            method_name="Float32",
            param_type="float32",
            byte_count=spec.byte_count,
            byte_writes=byte_writes,
            doc_comment=f"{description} ({spec.comment})",
            preamble="FLOAT_BITCAST",
        )
