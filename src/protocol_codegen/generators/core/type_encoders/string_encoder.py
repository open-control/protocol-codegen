"""
String Type Encoder.

Handles encoding of variable-length strings with length prefix.
"""

from __future__ import annotations

from protocol_codegen.generators.core.encoding_ops import MethodSpec
from protocol_codegen.generators.core.type_encoders.base import TypeEncoder


class StringEncoder(TypeEncoder):
    """Encoder for string type."""

    def supported_types(self) -> tuple[str, ...]:
        """Return supported types."""
        return ("string",)

    def get_method_spec(self, type_name: str, description: str) -> MethodSpec:
        """Generate MethodSpec for string encoding."""
        if type_name != "string":
            raise ValueError(f"Unsupported type: {type_name}")

        spec = self.strategy.get_string_spec()

        # String is special - uses loop, not fixed byte writes
        # We encode parameters in the preamble for the backend to parse
        return MethodSpec(
            type_name="string",
            method_name="String",
            param_type="string",
            byte_count=-1,  # Variable length
            byte_writes=(),  # Special handling by backend
            doc_comment=f"{description} ({spec.comment})",
            preamble=f"LENGTH_MASK=0x{spec.length_mask:02X};CHAR_MASK=0x{spec.char_mask:02X};MAX_LENGTH={spec.max_length}",
        )
