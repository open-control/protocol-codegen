"""
C++ Struct Generator - Unified for all protocols.

Generates Message*.hpp files from messages using the provided EncodingStrategy.
Uses common struct_utils for the actual generation logic.

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

from protocol_codegen.generators.core.naming import to_pascal_case
from protocol_codegen.generators.languages.cpp.file_generators.struct_utils import (
    generate_composite_structs,
    generate_decode_function,
    generate_encode_function,
    generate_footer,
    generate_header,
    generate_struct_definition,
)

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message
    from protocol_codegen.generators.protocols import EncodingStrategy


def generate_struct_hpp(
    message: Message,
    message_id: int,
    type_registry: TypeRegistry,
    output_path: Path,
    string_max_length: int,
    strategy: EncodingStrategy,
    include_message_name: bool | None = None,
) -> str:
    """
    Generate C++ struct header for a message using the provided encoding strategy.

    Args:
        message: Message instance to generate struct for
        message_id: Allocated MessageID for this message (e.g., 0x40)
        type_registry: TypeRegistry for resolving field types
        output_path: Path where struct .hpp will be written
        string_max_length: Maximum string length from config (e.g., 16)
        strategy: Encoding strategy (BinaryEncodingStrategy or SysExEncodingStrategy)
        include_message_name: Include MESSAGE_NAME prefix in payload (None = use strategy default)

    Returns:
        Generated C++ code as string
    """
    # Use strategy default if not specified
    if include_message_name is None:
        include_message_name = strategy.include_message_name_default

    # Convert SCREAMING_SNAKE_CASE to PascalCase
    pascal_name = to_pascal_case(message.name)
    struct_name = f"{pascal_name}Message"
    fields = message.fields
    description = f"{message.name} message"

    # Get encoding descriptions from strategy
    encoding_description = f"{strategy.description} ({strategy.name})"
    encoding_description_short = strategy.description.split()[0]  # "8-bit" or "7-bit"

    # Generate all parts using common utilities
    header = generate_header(
        struct_name=struct_name,
        description=description,
        fields=fields,
        type_registry=type_registry,
        encoding_description=encoding_description,
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
        encoding_description=encoding_description_short,
        include_message_name=include_message_name,
    )

    decode_fn = generate_decode_function(
        struct_name=struct_name,
        fields=fields,
        type_registry=type_registry,
        string_max_length=string_max_length,
        include_message_name=include_message_name,
    )

    footer = generate_footer()

    # Insert composite structs BEFORE main message struct
    full_code = f"{header}\n{composite_structs}\n{struct_def}\n{encode_fn}\n{decode_fn}\n{footer}}};\n\n}}  // namespace Protocol\n"
    return full_code
