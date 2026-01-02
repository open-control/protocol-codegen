"""
Java Struct Generator - Unified for all protocols.

Generates Message*.java files from messages using the provided EncodingStrategy.
Uses common struct_utils for the actual generation logic.

Key Features:
- Immutable classes (final fields)
- Calls Encoder.encodeXXX() instead of inline logic (DRY)
- Static factory decode() method
- MAX_PAYLOAD_SIZE constant for validation
- Clean getters following Java conventions

Generated Output:
- One .java file per message (e.g., TransportPlayMessage.java)
- ~80-120 lines per class (compact, readable)
- Package: Configurable via plugin_paths (e.g., protocol.struct)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.java.struct_utils import (
    collect_enum_names,
    generate_constructor,
    generate_decode_method,
    generate_encode_method,
    generate_field_declarations,
    generate_footer,
    generate_getters,
    generate_header,
    generate_inner_classes,
    generate_message_id_constant,
    needs_constants_import,
    needs_list_import,
)
from protocol_codegen.generators.common.naming import to_pascal_case

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message
    from protocol_codegen.generators.common.encoding import EncodingStrategy


def generate_struct_java(
    message: Message,
    message_id: int,
    type_registry: TypeRegistry,
    output_path: Path,
    string_max_length: int,
    package: str,
    strategy: EncodingStrategy,
    include_message_name: bool | None = None,
) -> str:
    """
    Generate Java message class for a message using the provided encoding strategy.

    Args:
        message: Message instance to generate class for
        message_id: Allocated message ID
        type_registry: TypeRegistry for resolving field types
        output_path: Path where message .java will be written
        string_max_length: Max string length from protocol config
        package: Java package name (e.g., 'protocol.struct')
        strategy: Encoding strategy (Serial8EncodingStrategy or SysExEncodingStrategy)
        include_message_name: Include MESSAGE_NAME prefix in payload (None = use strategy default)

    Returns:
        Generated Java code as string
    """
    # Use strategy default if not specified
    if include_message_name is None:
        include_message_name = strategy.include_message_name_default

    # Convert SCREAMING_SNAKE_CASE to PascalCase
    pascal_name = to_pascal_case(message.name)
    class_name = f"{pascal_name}Message"
    fields = message.fields
    description = f"{message.name} message"

    # Get encoding description from strategy
    encoding_description = f"{strategy.description} ({strategy.name})"

    # Analyze what imports are needed based on fields
    has_fields = len(fields) > 0
    enum_names = collect_enum_names(fields)

    # Generate all parts using common utilities
    header = generate_header(
        class_name=class_name,
        description=description,
        needs_encoder=has_fields,
        # Decoder is needed if there are fields OR if we need to skip message name prefix
        needs_decoder=has_fields or include_message_name,
        needs_list=needs_list_import(fields),
        needs_arraylist=needs_list_import(fields),
        needs_constants=needs_constants_import(fields, type_registry),
        enum_names=enum_names,
        package=package,
        encoding_description=encoding_description,
    )
    message_id_constant = generate_message_id_constant(
        message.name, pascal_name, include_message_name
    )
    inner_classes = generate_inner_classes(fields, type_registry)
    field_declarations = generate_field_declarations(fields, type_registry)
    constructor = generate_constructor(class_name, fields, type_registry)
    getters = generate_getters(fields, type_registry)
    encode_method = generate_encode_method(
        class_name=class_name,
        pascal_name=pascal_name,
        fields=fields,
        type_registry=type_registry,
        string_max_length=string_max_length,
        strategy=strategy,
        include_message_name=include_message_name,
    )
    decode_method = generate_decode_method(
        class_name=class_name,
        pascal_name=pascal_name,
        fields=fields,
        type_registry=type_registry,
        string_max_length=string_max_length,
        strategy=strategy,
        include_message_name=include_message_name,
    )
    footer = generate_footer()

    full_code = f"{header}\n{message_id_constant}\n{inner_classes}\n{field_declarations}\n{constructor}\n{getters}\n{encode_method}\n{decode_method}\n{footer}"
    return full_code
