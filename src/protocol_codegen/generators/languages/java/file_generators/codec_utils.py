"""
Java Encoder/Decoder call generation utilities.

Common functions for generating Java encode/decode function calls.
These are protocol-agnostic - the actual encoding logic is in the Encoder/Decoder classes.

Note: get_decoder_call is NOT extracted here because it depends on _get_encoded_size
which is protocol-specific (Binary vs SysEx have different size calculations).
This will be addressed in Phase 2 with the EncodingStrategy pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.core.naming import capitalize_first

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry


def get_encoder_call(field_name: str, field_type: str, type_registry: TypeRegistry) -> str:
    """
    Generate Encoder call for encoding a field.

    Returns:
        Java code line calling appropriate Encoder.encodeXxx() method
    """
    # Extract base type (handle arrays)
    base_type = field_type.split("[")[0]

    if not type_registry.is_atomic(base_type):
        raise ValueError(f"Unknown type: {base_type}")

    atomic = type_registry.get(base_type)

    if atomic.is_builtin:
        # Call Encoder.encodeXxx() - streaming, zero allocation
        encoder_name = f"encode{capitalize_first(base_type)}"
        return f"offset += Encoder.{encoder_name}(buffer, offset, {field_name});"
    else:
        # Nested struct - call its encodeTo()
        return f"offset += {field_name}.encodeTo(buffer, offset);"
