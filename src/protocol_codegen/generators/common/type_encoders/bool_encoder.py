"""
Bool Type Encoder.

Handles encoding of boolean values using strategy-specific true/false values.
"""

from __future__ import annotations

from protocol_codegen.generators.common.encoding.operations import (
    ByteWriteOp,
    MethodSpec,
)
from protocol_codegen.generators.common.type_encoders.base import TypeEncoder


class BoolEncoder(TypeEncoder):
    """Encoder for boolean type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("bool",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate MethodSpec for bool encoding."""
        if type_name != "bool":
            raise ValueError(f"Unsupported type: {type_name}")

        true_val = self.strategy.bool_true_value
        false_val = self.strategy.bool_false_value

        return MethodSpec(
            type_name="bool",
            method_name="Bool",
            param_type="bool",
            byte_count=1,
            byte_writes=(
                ByteWriteOp(
                    index=0,
                    expression=f"val ? 0x{true_val:02X} : 0x{false_val:02X}",
                ),
            ),
            doc_comment=f"{description} (0x{false_val:02X} or 0x{true_val:02X})",
        )
