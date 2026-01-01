"""
Integer Type Encoder.

Handles encoding of integer types: uint8, int8, uint16, int16, uint32, int32.
Uses EncodingStrategy to get protocol-specific byte layout.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.type_encoders.base import TypeEncoder


class IntegerEncoder(TypeEncoder):
    """Encoder for integer types."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("uint8", "int8", "uint16", "int16", "uint32", "int32")

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate MethodSpec for integer encoding."""
        if type_name not in self.supported_types():
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_integer_spec(type_name)
        if not spec:
            raise ValueError(f"No integer spec for {type_name}")

        # Build byte write operations
        byte_writes = tuple(
            ByteWriteOp(
                index=i,
                expression=(
                    f"val & 0x{mask:02X}"
                    if shift == 0
                    else f"(val >> {shift}) & 0x{mask:02X}"
                ),
            )
            for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True))
        )

        # Signed types need cast to unsigned for multi-byte
        needs_signed_cast = type_name.startswith("int") and spec.byte_count > 1

        # Method name: capitalize first letter of each word
        method_name = type_name[0].upper() + type_name[1:]

        return MethodSpec(
            type_name=type_name,
            method_name=method_name,
            param_type=type_name,
            byte_count=spec.byte_count,
            byte_writes=byte_writes,
            doc_comment=f"{description} ({spec.comment})",
            needs_signed_cast=needs_signed_cast,
        )
