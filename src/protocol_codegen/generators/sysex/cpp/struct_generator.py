"""
C++ Struct Generator for SysEx Protocol.

Generates Message*.hpp files from messages with 7-bit MIDI-safe encoding.
Uses common struct_utils with SysExEncodingStrategy for protocol-specific behavior.

Key Features:
- Calls Encoder::encodeXXX() instead of inline logic (DRY)
- MAX_PAYLOAD_SIZE constexpr for validation
- std::optional for safe decoding
- Zero runtime overhead (static inline + compiler optimization)

Generated Output:
- One .hpp file per message (e.g., TransportPlayMessage.hpp)
- ~60 lines per struct (vs ~350 with inline logic)
- Namespace: Protocol
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.cpp.struct_utils import (
    generate_composite_structs,
    generate_decode_function,
    generate_encode_function,
    generate_footer,
    generate_header,
    generate_struct_definition,
)
from protocol_codegen.generators.common.encoding import SysExEncodingStrategy
from protocol_codegen.generators.common.naming import to_pascal_case

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message


# Protocol-specific constants
ENCODING_DESCRIPTION = "7-bit MIDI-safe"
ENCODING_DESCRIPTION_SHORT = "7-bit"
DEFAULT_INCLUDE_MESSAGE_NAME = False
NEEDS_CSTRING = False
ALWAYS_ENCODE_ARRAY_COUNT = False


def generate_struct_hpp(
    message: Message,
    message_id: int,
    type_registry: TypeRegistry,
    output_path: Path,
    string_max_length: int,
    include_message_name: bool = DEFAULT_INCLUDE_MESSAGE_NAME,
) -> str:
    """
    Generate C++ struct header for a message using SysEx protocol.

    Args:
        message: Message instance to generate struct for
        message_id: Allocated MessageID for this message (e.g., 0x40)
        type_registry: TypeRegistry for resolving field types
        output_path: Path where struct .hpp will be written
        string_max_length: Maximum string length from config (e.g., 16)
        include_message_name: Include MESSAGE_NAME prefix in payload (default False)

    Returns:
        Generated C++ code as string

    Example:
        >>> transport_play = messages['TRANSPORT_PLAY']
        >>> code = generate_struct_hpp(transport_play, 0x40, registry, Path('TransportPlayMessage.hpp'), 16)
    """
    # Convert SCREAMING_SNAKE_CASE to PascalCase
    pascal_name = to_pascal_case(message.name)
    struct_name = f"{pascal_name}Message"
    fields = message.fields
    description = f"{message.name} message"

    # Get encoding strategy for SysEx
    strategy = SysExEncodingStrategy()

    # Generate all parts using common utilities
    header = generate_header(
        struct_name=struct_name,
        description=description,
        fields=fields,
        type_registry=type_registry,
        encoding_description=ENCODING_DESCRIPTION,
        needs_cstring=NEEDS_CSTRING,
    )

    # Generate composite structs FIRST (if any)
    composite_structs = generate_composite_structs(fields, type_registry)

    struct_def = generate_struct_definition(
        struct_name=struct_name,
        message_name=message.name,
        pascal_name=pascal_name,
        message_id=message_id,
        fields=fields,
        type_registry=type_registry,
        include_message_name=include_message_name,
    )

    encode_fn = generate_encode_function(
        struct_name=struct_name,
        pascal_name=pascal_name,
        fields=fields,
        type_registry=type_registry,
        string_max_length=string_max_length,
        strategy=strategy,
        encoding_description=ENCODING_DESCRIPTION_SHORT,
        include_message_name=include_message_name,
    )

    decode_fn = generate_decode_function(
        struct_name=struct_name,
        fields=fields,
        type_registry=type_registry,
        string_max_length=string_max_length,
        include_message_name=include_message_name,
        always_encode_array_count=ALWAYS_ENCODE_ARRAY_COUNT,
    )

    footer = generate_footer()

    # Insert composite structs BEFORE main message struct
    full_code = f"{header}\n{composite_structs}\n{struct_def}\n{encode_fn}\n{decode_fn}\n{footer}}};\n\n}}  // namespace Protocol\n"
    return full_code
