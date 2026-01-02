"""
C++ Encoder/Decoder call generation utilities.

Common functions for generating C++ encode/decode function calls.
These are protocol-agnostic - the actual encoding logic is in the Encoder/Decoder classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.core.naming import capitalize_first

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry


def get_cpp_type(field_type: str, type_registry: TypeRegistry) -> str:
    """
    Get C++ type for a field type string.

    Handles:
    - Builtin types (uint8 → uint8_t)
    - String (uses STRING_MAX_LENGTH constant instead of hardcoded <128>)
    - Array notation (uint8[8] → uint8_t[8])
    - Atomic types (ParameterValue → ParameterValue)

    Args:
        field_type: Type string from types.yaml
        type_registry: TypeRegistry instance

    Returns:
        C++ type string
    """
    # Check for array notation
    if "[" in field_type:
        base_type, array_size = field_type.split("[")
        array_size = array_size.rstrip("]")
        cpp_base = get_cpp_type(base_type, type_registry)
        return f"{cpp_base}[{array_size}]"

    # Get atomic type
    if type_registry.is_atomic(field_type):
        atomic = type_registry.get(field_type)
        if atomic.is_builtin:
            # Use std::string for string type
            if field_type == "string":
                return "std::string"
            assert atomic.cpp_type is not None
            return atomic.cpp_type
        else:
            # Custom atomic type - use struct name
            return atomic.name

    raise ValueError(f"Unknown type: {field_type}")


def get_encoder_call(field_name: str, field_type: str, type_registry: TypeRegistry) -> str:
    """
    Generate Encoder function call for encoding a field.

    Returns:
        C++ code line calling appropriate Encoder function
    """
    # Extract base type (handle arrays)
    base_type = field_type.split("[")[0]

    if not type_registry.is_atomic(base_type):
        raise ValueError(f"Unknown type: {base_type}")

    atomic = type_registry.get(base_type)

    if atomic.is_builtin:
        # Call Encoder::encodeXXX() (static method in Encoder struct)
        encoder_name = f"encode{capitalize_first(base_type)}"
        return f"Encoder::{encoder_name}(ptr, {field_name});"
    else:
        # Nested struct - call its encode()
        return f"ptr += {field_name}.encode(ptr, bufferSize - (ptr - buffer));"


def get_decoder_call(
    field_name: str, field_type: str, type_registry: TypeRegistry, direct_target: str | None = None
) -> str:
    """
    Generate decoder function call for decoding a field.

    Args:
        field_name: Variable name for temporary storage (if direct_target is None)
        field_type: Type string
        type_registry: Type registry
        direct_target: Optional direct struct member path (e.g., "pageInfo_data.pageIndex")

    Returns:
        C++ code line(s) calling appropriate decoder function
    """
    base_type = field_type.split("[")[0]

    if not type_registry.is_atomic(base_type):
        raise ValueError(f"Unknown type: {base_type}")

    atomic = type_registry.get(base_type)
    cpp_type = get_cpp_type(base_type, type_registry)

    if atomic.is_builtin:
        decoder_name = f"decode{capitalize_first(base_type)}"
        target = direct_target if direct_target else field_name

        # All types use the same call pattern now (no template for string)
        decoder_call = f"Decoder::{decoder_name}(ptr, remaining, {target})"

        # OPTION B: Direct pattern if direct_target provided
        if direct_target:
            return f"if (!{decoder_call}) return std::nullopt;"
        else:
            return f"""{cpp_type} {field_name};
        if (!{decoder_call}) return std::nullopt;"""
    else:
        return f"""auto {field_name} = {base_type}::decode(ptr, remaining);
        if (!{field_name}) return std::nullopt;
        ptr += {base_type}::MAX_PAYLOAD_SIZE;
        remaining -= {base_type}::MAX_PAYLOAD_SIZE;"""
