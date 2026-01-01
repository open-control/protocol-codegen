"""
Java Struct Generator
Generates Message*.java files from messages with Encoder calls.

This generator creates immutable Java classes that call Encoder methods
instead of duplicating encoding logic. This achieves significant code
reduction while maintaining clean separation of concerns.

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

# Import field classes for runtime isinstance checks
from protocol_codegen.core.field import CompositeField, EnumField, FieldBase, PrimitiveField
from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy
from protocol_codegen.generators.common.java.codec_utils import get_encoder_call
from protocol_codegen.generators.common.naming import (
    capitalize_first,
    field_to_pascal_case,
    to_pascal_case,
)
from protocol_codegen.generators.common.payload_calculator import PayloadCalculator

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message


def generate_struct_java(
    message: Message,
    message_id: int,
    type_registry: TypeRegistry,
    output_path: Path,
    string_max_length: int,
    package: str,
    include_message_name: bool = True,
) -> str:
    """
    Generate Java message class for a message.

    Args:
        message: Message instance to generate class for
        message_id: Allocated message ID
        type_registry: TypeRegistry for resolving field types
        output_path: Path where message .java will be written
        string_max_length: Max string length from protocol config
        package: Java package name (e.g., 'protocol.struct')
        include_message_name: Include MESSAGE_NAME prefix in payload (default True)

    Returns:
        Generated Java code as string

    Example:
        >>> transport_play = messages['TRANSPORT_PLAY']
        >>> code = generate_struct_java(transport_play, 0x01, registry, Path('TransportPlayMessage.java'), 16, 'protocol.struct')
    """
    # Convert SCREAMING_SNAKE_CASE to PascalCase
    pascal_name = to_pascal_case(message.name)
    class_name = f"{pascal_name}Message"
    fields = message.fields
    description = f"{message.name} message"

    # Analyze what imports are needed based on fields
    needs_encoder = len(fields) > 0
    needs_decoder = len(fields) > 0
    needs_list = _needs_list_import(fields)
    needs_arraylist = _needs_list_import(fields)
    needs_constants = _needs_constants_import(fields, type_registry)
    enum_names = _collect_enum_names(fields)

    header = _generate_header(
        class_name,
        description,
        needs_encoder,
        needs_decoder,
        needs_list,
        needs_arraylist,
        needs_constants,
        enum_names,
        package,
    )
    message_id_constant = _generate_message_id_constant(message.name, pascal_name, include_message_name)
    inner_classes = _generate_inner_classes(fields, type_registry)
    field_declarations = _generate_field_declarations(fields, type_registry)
    constructor = _generate_constructor(class_name, fields, type_registry)
    getters = _generate_getters(fields, type_registry)
    encode_method = _generate_encode_method(
        class_name, pascal_name, fields, type_registry, string_max_length, include_message_name
    )
    decode_method = _generate_decode_method(
        class_name, pascal_name, fields, type_registry, string_max_length, include_message_name
    )
    footer = _generate_footer()

    full_code = f"{header}\n{message_id_constant}\n{inner_classes}\n{field_declarations}\n{constructor}\n{getters}\n{encode_method}\n{decode_method}\n{footer}"
    return full_code


def _collect_enum_names(fields: Sequence[FieldBase]) -> set[str]:
    """
    Collect all non-bitflags enum names from fields (recursively).

    Bitflags enums are int types and don't need imports.
    Regular enums need to be imported.
    """
    enum_names: set[str] = set()

    def collect_from_fields(field_list: Sequence[FieldBase]) -> None:
        for field in field_list:
            if isinstance(field, EnumField):
                # Only add non-bitflags enums (bitflags are int, no import needed)
                if not field.enum_def.is_bitflags:
                    enum_names.add(field.enum_def.name)
            elif isinstance(field, CompositeField):
                collect_from_fields(field.fields)

    collect_from_fields(fields)
    return enum_names


def _generate_header(
    class_name: str,
    description: str,
    needs_encoder: bool,
    needs_decoder: bool,
    needs_list: bool,
    needs_arraylist: bool,
    needs_constants: bool,
    enum_names: set[str],
    package: str,
) -> str:
    """Generate file header with package and class declaration, importing only what's needed."""
    # Extract base package for imports
    # If package is "protocol.struct", base is "protocol"
    # If package is "protocol", base is "protocol"
    base_package = package.rsplit(".", 1)[0] if "." in package else package

    imports = [f"import {base_package}.MessageID;"]

    if needs_encoder:
        imports.append(f"import {base_package}.Encoder;")
    if needs_decoder:
        imports.append(f"import {base_package}.Decoder;")
    if needs_constants:
        imports.append(f"import {base_package}.ProtocolConstants;")

    # Add enum imports (non-bitflags only)
    for enum_name in sorted(enum_names):
        imports.append(f"import {base_package}.{enum_name};")

    if needs_list:
        imports.append("import java.util.List;")
    if needs_arraylist:
        imports.append("import java.util.ArrayList;")

    imports_str = "\n".join(imports)

    return f"""package {package};

{imports_str}

/**
 * {class_name} - Auto-generated Protocol Message
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: types.yaml
 *
 * Description: {description}
 *
 * This class is immutable and uses Encoder for encode/decode operations.
 * All encoding is 8-bit binary (Serial8).
 */
public final class {class_name} {{
"""


def _generate_message_id_constant(message_name: str, pascal_name: str, include_message_name: bool = True) -> str:
    """Generate MESSAGE_ID and MESSAGE_NAME constants for auto-detection and logging."""
    lines = [
        "",
        "    // ============================================================================",
        "    // Auto-detected MessageID for protocol.send()",
        "    // ============================================================================",
        "",
        f"    public static final MessageID MESSAGE_ID = MessageID.{message_name};",
    ]

    if include_message_name:
        lines.extend([
            "",
            "    // Message name for logging (encoded in payload)",
            f'    public static final String MESSAGE_NAME = "{pascal_name}";',
        ])

    lines.append("")
    return "\n".join(lines)


def _generate_field_declarations(fields: Sequence[FieldBase], type_registry: TypeRegistry) -> str:
    """Generate private final field declarations (supports composites and enums)."""
    lines: list[str] = [
        "    // ============================================================================"
    ]
    lines.append("    // Fields")
    lines.append(
        "    // ============================================================================"
    )
    lines.append("")

    for field in fields:
        if isinstance(field, EnumField):
            # Enum field - use enum's Java type
            java_type = field.enum_def.java_type
            if field.is_array():
                lines.append(f"    private final {java_type}[] {field.name};")
            else:
                lines.append(f"    private final {java_type} {field.name};")
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            java_type = _get_java_type(field_type_name, type_registry)
            if field.is_array():
                # Primitive arrays use T[] (no boxing, zero-allocation)
                lines.append(f"    private final {java_type}[] {field.name};")
            else:
                lines.append(f"    private final {java_type} {field.name};")
        elif isinstance(field, CompositeField):
            # Composite field
            class_name = field_to_pascal_case(field.name)
            if field.array:
                # Composite arrays use T[] (aligned with C++ std::array)
                lines.append(f"    private final {class_name}[] {field.name};")
            else:
                lines.append(f"    private final {class_name} {field.name};")

    lines.append("")
    return "\n".join(lines)


def _generate_constructor(
    class_name: str, fields: Sequence[FieldBase], type_registry: TypeRegistry
) -> str:
    """Generate public constructor."""
    lines: list[str] = [
        "    // ============================================================================"
    ]
    lines.append("    // Constructor")
    lines.append(
        "    // ============================================================================"
    )
    lines.append("")
    lines.append("    /**")
    lines.append(f"     * Construct a new {class_name}")
    lines.append("     *")

    # Add parameter docs
    for field in fields:
        lines.append(f"     * @param {field.name} The {field.name} value")

    lines.append("     */")

    # Constructor signature
    params: list[str] = []
    for field in fields:
        if isinstance(field, EnumField):
            java_type = field.enum_def.java_type
            if field.is_array():
                params.append(f"{java_type}[] {field.name}")
            else:
                params.append(f"{java_type} {field.name}")
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            java_type = _get_java_type(field_type_name, type_registry)
            if field.is_array():
                # Primitive arrays use T[] (no boxing)
                params.append(f"{java_type}[] {field.name}")
            else:
                params.append(f"{java_type} {field.name}")
        elif isinstance(field, CompositeField):
            # Composite field
            class_name_inner = field_to_pascal_case(field.name)
            if field.array:
                # Composite arrays use T[] (aligned with C++ std::array)
                params.append(f"{class_name_inner}[] {field.name}")
            else:
                params.append(f"{class_name_inner} {field.name}")

    param_str = ", ".join(params)
    lines.append(f"    public {class_name}({param_str}) {{")

    # Assignments
    for field in fields:
        lines.append(f"        this.{field.name} = {field.name};")

    lines.append("    }")
    lines.append("")

    return "\n".join(lines)


def _generate_getters(fields: Sequence[FieldBase], type_registry: TypeRegistry) -> str:
    """Generate public getters."""
    lines: list[str] = [
        "    // ============================================================================"
    ]
    lines.append("    // Getters")
    lines.append(
        "    // ============================================================================"
    )
    lines.append("")

    for field in fields:
        if isinstance(field, EnumField):
            java_type = field.enum_def.java_type
            if field.is_array():
                java_type = f"{java_type}[]"
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            java_type = _get_java_type(field_type_name, type_registry)
            if field.is_array():
                # Primitive arrays use T[] (no boxing)
                java_type = f"{java_type}[]"
        elif isinstance(field, CompositeField):
            class_name = field_to_pascal_case(field.name)
            # Composite arrays use T[] (aligned with C++ std::array)
            java_type = f"{class_name}[]" if field.array else class_name
        else:
            continue  # Unknown field type

        getter_name = _to_getter_name(field.name)

        lines.append("    /**")
        lines.append(f"     * Get the {field.name} value")
        lines.append("     *")
        lines.append(f"     * @return {field.name}")
        lines.append("     */")
        lines.append(f"    public {java_type} {getter_name}() {{")
        lines.append(f"        return {field.name};")
        lines.append("    }")
        lines.append("")

    return "\n".join(lines)


def _generate_encode_method(
    class_name: str,
    pascal_name: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    string_max_length: int,
    include_message_name: bool = True,
) -> str:
    """Generate encode() method calling Encoder (streaming, zero-allocation)."""
    # Calculate max payload size using PayloadCalculator
    name_prefix_size = (1 + len(pascal_name)) if include_message_name else 0
    calculator = PayloadCalculator(Serial8EncodingStrategy(), type_registry)
    max_size = calculator.calculate_max_payload_size(
        fields, string_max_length, name_prefix_size
    )

    lines: list[str] = [
        "    // ============================================================================"
    ]
    lines.append("    // Encoding")
    lines.append(
        "    // ============================================================================"
    )
    lines.append("")
    lines.append("    /**")
    lines.append("     * Maximum payload size in bytes (8-bit encoded)")
    lines.append("     */")
    lines.append(f"    public static final int MAX_PAYLOAD_SIZE = {max_size};")
    lines.append("")

    # Generate encode(buffer, offset) method - streaming, zero-allocation
    lines.append("    /**")
    lines.append("     * Encode message directly into provided buffer (zero allocation)")
    lines.append("     *")
    lines.append("     * @param buffer Output buffer (must have enough space)")
    lines.append("     * @param startOffset Starting position in buffer")
    lines.append("     * @return Number of bytes written")
    lines.append("     */")
    lines.append("    public int encode(byte[] buffer, int startOffset) {")
    lines.append("        int offset = startOffset;")
    lines.append("")

    # Conditionally encode MESSAGE_NAME
    if include_message_name:
        lines.append("        // Encode message name (length-prefixed string for bridge logging)")
        lines.append("        buffer[offset++] = (byte) MESSAGE_NAME.length();")
        lines.append("        for (int i = 0; i < MESSAGE_NAME.length(); i++) {")
        lines.append("            buffer[offset++] = (byte) MESSAGE_NAME.charAt(i);")
        lines.append("        }")
        lines.append("")

    # Empty messages
    if not fields:
        lines.append("        return offset - startOffset;")
        lines.append("    }")
        lines.append("")
        return "\n".join(lines)

    # Add encode calls for each field
    for field in fields:
        if isinstance(field, EnumField):
            # Enum field - encode as uint8
            # Bitflags are int (no getValue needed), regular enums use getValue()
            is_bitflags = field.enum_def.is_bitflags
            if field.is_array():
                lines.append(
                    f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.length);"
                )
                lines.append("")
                java_type = field.enum_def.java_type
                lines.append(f"        for ({java_type} item : {field.name}) {{")
                if is_bitflags:
                    lines.append("            offset += Encoder.writeUint8(buffer, offset, item);")
                else:
                    lines.append("            offset += Encoder.writeUint8(buffer, offset, item.getValue());")
                lines.append("        }")
                lines.append("")
            else:
                if is_bitflags:
                    lines.append(
                        f"        offset += Encoder.writeUint8(buffer, offset, {field.name});"
                    )
                else:
                    lines.append(
                        f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.getValue());"
                    )
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            if field.is_array():
                # Primitive arrays use .length (no boxing)
                lines.append(
                    f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.length);"
                )
                lines.append("")
                lines.append(
                    f"        for ({_get_java_type(field_type_name, type_registry)} item : {field.name}) {{"
                )
                encoder_call = get_encoder_call("item", field_type_name, type_registry)
                lines.append(f"            {encoder_call}")
                lines.append("        }")
                lines.append("")
            else:
                encoder_call = get_encoder_call(field.name, field_type_name, type_registry)
                lines.append(f"        {encoder_call}")
        elif isinstance(field, CompositeField):
            # Composite field
            if field.array:
                lines.append(
                    f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.length);"
                )
                lines.append("")
                class_name_inner = field_to_pascal_case(field.name)
                lines.append(f"        for ({class_name_inner} item : {field.name}) {{")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        getter_name = _to_getter_name(nested_field.name)
                        is_bitflags = nested_field.enum_def.is_bitflags
                        if nested_field.is_array():
                            java_type = nested_field.enum_def.java_type
                            lines.append(
                                f"            offset += Encoder.writeUint8(buffer, offset, item.{getter_name}().length);"
                            )
                            lines.append(f"            for ({java_type} e : item.{getter_name}()) {{")
                            if is_bitflags:
                                lines.append(
                                    "                offset += Encoder.writeUint8(buffer, offset, e);"
                                )
                            else:
                                lines.append(
                                    "                offset += Encoder.writeUint8(buffer, offset, e.getValue());"
                                )
                            lines.append("            }")
                        else:
                            if is_bitflags:
                                lines.append(
                                    f"            offset += Encoder.writeUint8(buffer, offset, item.{getter_name}());"
                                )
                            else:
                                lines.append(
                                    f"            offset += Encoder.writeUint8(buffer, offset, item.{getter_name}().getValue());"
                                )
                    elif isinstance(nested_field, PrimitiveField):
                        getter_name = _to_getter_name(nested_field.name)
                        if nested_field.is_array():
                            java_type = _get_java_type(nested_field.type_name.value, type_registry)
                            lines.append(
                                f"            offset += Encoder.writeUint8(buffer, offset, item.{getter_name}().length);"
                            )
                            lines.append(
                                f"            for ({java_type} type : item.{getter_name}()) {{"
                            )
                            encoder_call = get_encoder_call(
                                "type", nested_field.type_name.value, type_registry
                            )
                            lines.append(f"                {encoder_call}")
                            lines.append("            }")
                        else:
                            encoder_call = get_encoder_call(
                                f"item.{getter_name}()", nested_field.type_name.value, type_registry
                            )
                            lines.append(f"            {encoder_call}")
                lines.append("        }")
                lines.append("")
            else:
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        getter_name = _to_getter_name(nested_field.name)
                        is_bitflags = nested_field.enum_def.is_bitflags
                        if is_bitflags:
                            lines.append(
                                f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.{getter_name}());"
                            )
                        else:
                            lines.append(
                                f"        offset += Encoder.writeUint8(buffer, offset, {field.name}.{getter_name}().getValue());"
                            )
                    elif isinstance(nested_field, PrimitiveField):
                        getter_name = _to_getter_name(nested_field.name)
                        encoder_call = get_encoder_call(
                            f"{field.name}.{getter_name}()",
                            nested_field.type_name.value,
                            type_registry,
                        )
                        lines.append(f"        {encoder_call}")

    lines.append("")
    lines.append("        return offset - startOffset;")
    lines.append("    }")
    lines.append("")

    return "\n".join(lines)


def _generate_decode_method(
    class_name: str,
    pascal_name: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    string_max_length: int,
    include_message_name: bool = True,
) -> str:
    """Generate static decode() factory method."""
    # Calculate min payload size using PayloadCalculator
    name_prefix_size = (1 + len(pascal_name)) if include_message_name else 0
    calculator = PayloadCalculator(Serial8EncodingStrategy(), type_registry)
    min_size = calculator.calculate_min_payload_size(
        fields, string_max_length, name_prefix_size
    )

    lines: list[str] = [
        "    // ============================================================================"
    ]
    lines.append("    // Decoding")
    lines.append(
        "    // ============================================================================"
    )
    lines.append("")

    # Simplified decode for empty messages
    if not fields:
        if include_message_name:
            # With MESSAGE_NAME - need to skip prefix
            lines.append("    /**")
            lines.append("     * Minimum payload size in bytes (message name only)")
            lines.append("     */")
            lines.append(f"    private static final int MIN_PAYLOAD_SIZE = {min_size};")
            lines.append("")
            lines.append("    /**")
            lines.append("     * Decode message from MIDI-safe bytes (message name only, no fields)")
            lines.append("     * @param data Input buffer")
            lines.append(f"     * @return New {class_name} instance")
            lines.append("     * @throws IllegalArgumentException if data is invalid or insufficient")
            lines.append("     */")
            lines.append(f"    public static {class_name} decode(byte[] data) {{")
            lines.append("        if (data.length < MIN_PAYLOAD_SIZE) {")
            lines.append(
                f'            throw new IllegalArgumentException("Insufficient data for {class_name} decode");'
            )
            lines.append("        }")
            lines.append("")
            lines.append("        int offset = 0;")
            lines.append("")
            lines.append("        // Skip message name prefix (length + name bytes)")
            lines.append("        int nameLen = data[offset++] & 0xFF;")
            lines.append("        offset += nameLen;")
            lines.append("")
            lines.append(f"        return new {class_name}();")
            lines.append("    }")
            lines.append("")
        else:
            # No MESSAGE_NAME - just return new instance
            lines.append("    /**")
            lines.append("     * Decode message from bytes (no fields)")
            lines.append("     * @param data Input buffer (unused for empty message)")
            lines.append(f"     * @return New {class_name} instance")
            lines.append("     */")
            lines.append(f"    public static {class_name} decode(byte[] data) {{")
            lines.append(f"        return new {class_name}();")
            lines.append("    }")
            lines.append("")
        return "\n".join(lines)

    # Standard decode needs MIN_PAYLOAD_SIZE for validation
    lines.append("    /**")
    lines.append("     * Minimum payload size in bytes (with empty strings)")
    lines.append("     */")
    lines.append(f"    private static final int MIN_PAYLOAD_SIZE = {min_size};")
    lines.append("")

    # Standard decode for messages with fields
    lines.append("    /**")
    lines.append("     * Decode message from MIDI-safe bytes")
    lines.append("     *")
    lines.append("     * @param data Input buffer with encoded data")
    lines.append(f"     * @return Decoded {class_name} instance")
    lines.append("     * @throws IllegalArgumentException if data is invalid or insufficient")
    lines.append("     */")
    lines.append(f"    public static {class_name} decode(byte[] data) {{")
    lines.append("        if (data.length < MIN_PAYLOAD_SIZE) {")
    lines.append(
        f'            throw new IllegalArgumentException("Insufficient data for {class_name} decode");'
    )
    lines.append("        }")
    lines.append("")
    lines.append("        int offset = 0;")
    lines.append("")

    # Conditionally skip MESSAGE_NAME prefix
    if include_message_name:
        lines.append("        // Skip message name prefix (length + name bytes)")
        lines.append("        int nameLen = data[offset++] & 0xFF;")
        lines.append("        offset += nameLen;")
    lines.append("")

    # Add decode calls for each field
    field_vars: list[str] = []
    for field in fields:
        if isinstance(field, EnumField):
            # Enum field - decode uint8 and convert to enum
            # Bitflags are int (no fromValue needed), regular enums use fromValue()
            java_type = field.enum_def.java_type
            is_bitflags = field.enum_def.is_bitflags
            if field.is_array():
                lines.append(f"        int count_{field.name} = Decoder.decodeUint8(data, offset);")
                lines.append("        offset += 1;")
                lines.append("")
                lines.append(
                    f"        {java_type}[] {field.name} = new {java_type}[count_{field.name}];"
                )
                lines.append(f"        for (int i = 0; i < count_{field.name}; i++) {{")
                if is_bitflags:
                    lines.append(
                        f"            {field.name}[i] = Decoder.decodeUint8(data, offset);"
                    )
                else:
                    lines.append(
                        f"            {field.name}[i] = {java_type}.fromValue(Decoder.decodeUint8(data, offset));"
                    )
                lines.append("            offset += 1;")
                lines.append("        }")
                lines.append("")
            else:
                if is_bitflags:
                    lines.append(
                        f"        {java_type} {field.name} = Decoder.decodeUint8(data, offset);"
                    )
                else:
                    lines.append(
                        f"        {java_type} {field.name} = {java_type}.fromValue(Decoder.decodeUint8(data, offset));"
                    )
                lines.append("        offset += 1;")
                lines.append("")
            field_vars.append(field.name)
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            java_type = _get_java_type(field_type_name, type_registry)
            if field.is_array():
                # Primitive array - use T[] (no boxing, zero-allocation)
                lines.append(f"        int count_{field.name} = Decoder.decodeUint8(data, offset);")
                lines.append("        offset += 1;")
                lines.append("")
                lines.append(
                    f"        {java_type}[] {field.name} = new {java_type}[count_{field.name}];"
                )
                lines.append(f"        for (int i = 0; i < count_{field.name}; i++) {{")
                # Generate array assignment directly (avoid variable declaration)
                decoder_name = f"decode{capitalize_first(field_type_name)}"
                if field_type_name == "string":
                    lines.append(
                        f"            {field.name}[i] = Decoder.{decoder_name}(data, offset, ProtocolConstants.STRING_MAX_LENGTH);"
                    )
                    lines.append(f"            offset += 1 + {field.name}[i].length();")
                else:
                    encoded_size = _get_encoded_size(field_type_name, 0)
                    lines.append(
                        f"            {field.name}[i] = Decoder.{decoder_name}(data, offset);"
                    )
                    lines.append(f"            offset += {encoded_size};")
                lines.append("        }")
                lines.append("")
                field_vars.append(field.name)
            else:
                # Scalar primitive
                decoder_call = _get_decoder_call(
                    field.name, field_type_name, java_type, type_registry
                )
                lines.append(f"        {decoder_call}")
                field_vars.append(field.name)
        elif isinstance(field, CompositeField):
            if field.array:
                # Decode array count
                lines.append(f"        int count_{field.name} = Decoder.decodeUint8(data, offset);")
                lines.append("        offset += 1;")
                lines.append("")
                # Decode items into array (aligned with C++ std::array)
                composite_class = field_to_pascal_case(field.name)
                lines.append(
                    f"        {composite_class}[] {field.name} = new {composite_class}[count_{field.name}];"
                )
                lines.append(f"        for (int i = 0; i < count_{field.name}; i++) {{")
                # Decode each nested field
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        # Nested enum field
                        nested_java_type = nested_field.enum_def.java_type
                        is_bitflags = nested_field.enum_def.is_bitflags
                        if nested_field.is_array():
                            lines.append(
                                f"            byte count_{nested_field.name} = (byte) Decoder.decodeUint8(data, offset);"
                            )
                            lines.append("            offset += 1;")
                            lines.append(
                                f"            {nested_java_type}[] item_{nested_field.name} = new {nested_java_type}[count_{nested_field.name}];"
                            )
                            lines.append(
                                f"            for (int j = 0; j < count_{nested_field.name} && j < {nested_field.array}; j++) {{"
                            )
                            if is_bitflags:
                                lines.append(
                                    f"                item_{nested_field.name}[j] = Decoder.decodeUint8(data, offset);"
                                )
                            else:
                                lines.append(
                                    f"                item_{nested_field.name}[j] = {nested_java_type}.fromValue(Decoder.decodeUint8(data, offset));"
                                )
                            lines.append("                offset += 1;")
                            lines.append("            }")
                        else:
                            if is_bitflags:
                                lines.append(
                                    f"            {nested_java_type} item_{nested_field.name} = Decoder.decodeUint8(data, offset);"
                                )
                            else:
                                lines.append(
                                    f"            {nested_java_type} item_{nested_field.name} = {nested_java_type}.fromValue(Decoder.decodeUint8(data, offset));"
                                )
                            lines.append("            offset += 1;")
                    elif isinstance(nested_field, PrimitiveField):
                        java_type = _get_java_type(nested_field.type_name.value, type_registry)
                        if nested_field.is_array():
                            # Nested array of primitives - decode count for dynamic arrays
                            lines.append(
                                f"            byte count_{nested_field.name} = (byte) Decoder.decodeUint8(data, offset);"
                            )
                            lines.append("            offset += 1;")
                            lines.append(
                                f"            {java_type}[] item_{nested_field.name} = new {java_type}[count_{nested_field.name}];"
                            )
                            lines.append(
                                f"            for (int j = 0; j < count_{nested_field.name} && j < {nested_field.array}; j++) {{"
                            )
                            decoder_call = _get_decoder_call(
                                f"item_{nested_field.name}_j",
                                nested_field.type_name.value,
                                java_type,
                                type_registry,
                            )
                            # Indent by 16 spaces (4 levels)
                            for line in decoder_call.split("\n"):
                                lines.append(f"        {line}")
                            lines.append(
                                f"                item_{nested_field.name}[j] = item_{nested_field.name}_j;"
                            )
                            lines.append("            }")
                        else:
                            decoder_call = _get_decoder_call(
                                f"item_{nested_field.name}",
                                nested_field.type_name.value,
                                java_type,
                                type_registry,
                            )
                            for line in decoder_call.split("\n"):
                                lines.append(f"    {line}")
                # Construct item and assign to array
                item_params: list[str] = []
                for nested_field in field.fields:
                    if isinstance(nested_field, (EnumField, PrimitiveField)):
                        item_params.append(f"item_{nested_field.name}")
                item_params_str = ", ".join(item_params)
                lines.append(
                    f"            {field.name}[i] = new {field_to_pascal_case(field.name)}({item_params_str});"
                )
                lines.append("        }")
                lines.append("")
                field_vars.append(field.name)
            else:
                # Single composite - decode nested fields
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        nested_java_type = nested_field.enum_def.java_type
                        is_bitflags = nested_field.enum_def.is_bitflags
                        if is_bitflags:
                            lines.append(
                                f"        {nested_java_type} {field.name}_{nested_field.name} = Decoder.decodeUint8(data, offset);"
                            )
                        else:
                            lines.append(
                                f"        {nested_java_type} {field.name}_{nested_field.name} = {nested_java_type}.fromValue(Decoder.decodeUint8(data, offset));"
                            )
                        lines.append("        offset += 1;")
                    elif isinstance(nested_field, PrimitiveField):
                        java_type = _get_java_type(nested_field.type_name.value, type_registry)
                        decoder_call = _get_decoder_call(
                            f"{field.name}_{nested_field.name}",
                            nested_field.type_name.value,
                            java_type,
                            type_registry,
                        )
                        lines.append(f"        {decoder_call}")
                # Construct composite
                composite_params: list[str] = []
                for nested_field in field.fields:
                    if isinstance(nested_field, (EnumField, PrimitiveField)):
                        composite_params.append(f"{field.name}_{nested_field.name}")
                composite_params_str = ", ".join(composite_params)
                lines.append(
                    f"        {field_to_pascal_case(field.name)} {field.name} = new {field_to_pascal_case(field.name)}({composite_params_str});"
                )
                lines.append("")
                field_vars.append(field.name)

    # Construct and return instance
    field_list = ", ".join(field_vars)
    lines.append("")
    lines.append(f"        return new {class_name}({field_list});")
    lines.append("    }")
    lines.append("")

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate class closing."""
    return "}  // class Message\n"





def _get_java_type(field_type: str, type_registry: TypeRegistry) -> str:
    """
    Get Java type for a field type string.

    Handles:
    - Builtin types (uint8 → byte, float32 → float)
    - Array notation (uint8[8] → byte[])
    - Atomic types (ParameterValue → ParameterValueMessage)

    Args:
        field_type: Type string from types.yaml
        type_registry: TypeRegistry instance

    Returns:
        Java type string
    """
    # Check for array notation
    if "[" in field_type:
        base_type, array_size = field_type.split("[")
        array_size = array_size.rstrip("]")
        java_base = _get_java_type(base_type, type_registry)
        return f"{java_base}[]"

    # Get atomic type
    if type_registry.is_atomic(field_type):
        atomic = type_registry.get(field_type)
        if atomic.is_builtin:
            java_type = atomic.java_type
            if java_type is None:
                raise ValueError(f"Missing Java type mapping for builtin type: {field_type}")
            return java_type
        else:
            # Custom atomic type - use class name with Message suffix
            return f"{atomic.name}Message"

    raise ValueError(f"Unknown type: {field_type}")


def _get_decoder_call(
    field_name: str, field_type: str, java_type: str, type_registry: TypeRegistry
) -> str:
    """
    Generate Encoder method call for decoding a field.

    Returns:
        Java code lines calling appropriate Encoder method
    """
    base_type = field_type.split("[")[0]

    if not type_registry.is_atomic(base_type):
        raise ValueError(f"Unknown type: {base_type}")

    atomic = type_registry.get(base_type)

    if atomic.is_builtin:
        # Call Encoder.decodeXXX()
        decoder_name = f"decode{capitalize_first(base_type)}"

        if base_type == "string":
            # String needs max length parameter (using ProtocolConstants.STRING_MAX_LENGTH from config)
            return f"{java_type} {field_name} = Decoder.{decoder_name}(data, offset, ProtocolConstants.STRING_MAX_LENGTH);\n        offset += 1 + {field_name}.length();"
        else:
            # Other types - calculate size based on type
            encoded_size = _get_encoded_size(base_type, 0)  # Size hardcoded per type
            return f"{java_type} {field_name} = Decoder.{decoder_name}(data, offset);\n        offset += {encoded_size};"
    else:
        # Nested struct - call its decode()
        return f"{java_type} {field_name} = {java_type}.decode(data);\n        offset += {java_type}.MAX_PAYLOAD_SIZE;"


def _get_encoded_size(type_name: str, raw_size: int) -> int:
    """
    Get encoded size for a builtin type in 8-bit protocol.

    For Serial8 protocol, there's no expansion - sizes are raw.

    Args:
        type_name: Builtin type name (e.g., 'bool', 'uint8', 'float32')
        raw_size: Raw size in bytes (unused for known types)

    Returns:
        Encoded size in bytes
    """
    # 8-bit protocol: no expansion
    # bool: 1 byte
    if type_name == "bool":
        return 1

    # uint8, int8, norm8: 1 byte
    if type_name in ("uint8", "int8", "norm8"):
        return 1

    # uint16, int16, norm16: 2 bytes
    if type_name in ("uint16", "int16", "norm16"):
        return 2

    # uint32, int32, float32: 4 bytes
    if type_name in ("uint32", "int32", "float32"):
        return 4

    # Default: return raw size
    return raw_size


def _to_getter_name(field_name: str) -> str:
    """
    Convert field name to getter name.

    Examples:
        value → getValue
        isActive → isActive
        maxValue → getMaxValue

    Args:
        field_name: Field name

    Returns:
        Getter method name
    """
    # Special case for boolean fields starting with "is"
    if field_name.startswith("is") and len(field_name) > 2 and field_name[2].isupper():
        return field_name

    # Standard getter
    return f"get{field_name[0].upper()}{field_name[1:]}"


# ============================================================================
# COMPOSITE FIELD SUPPORT (Phase 5 - Java)
# ============================================================================


def _generate_inner_classes(
    fields: Sequence[FieldBase], type_registry: TypeRegistry, depth: int = 0
) -> str:
    """
    Recursively generate inner static classes for composite fields.

    Returns empty string if no composites found.
    Safety: Max depth 3 to prevent infinite recursion.
    """
    if depth > 3:
        return ""

    classes: list[str] = []
    for field in fields:
        if isinstance(field, CompositeField):
            # Generate nested composites first (depth-first like C++)
            nested = _generate_inner_classes(field.fields, type_registry, depth + 1)
            if nested:
                classes.append(nested)

            # Generate this composite class
            class_code = _generate_single_inner_class(field, type_registry)
            classes.append(class_code)
        # EnumField and PrimitiveField don't need inner classes

    return "\n".join(classes)


def _generate_single_inner_class(field: CompositeField, type_registry: TypeRegistry) -> str:
    """Generate a single inner static class for a composite field."""
    class_name = field_to_pascal_case(field.name)

    lines: list[str] = [
        "    // ============================================================================",
        f"    // Inner Class: {class_name}",
        "    // ============================================================================",
        "",
        f"    public static final class {class_name} {{",
    ]

    # Fields
    for nested_field in field.fields:
        if isinstance(nested_field, PrimitiveField):
            java_type = _get_java_type(nested_field.type_name.value, type_registry)
            if nested_field.is_array():
                # Primitive array in inner class (e.g., childrenTypes which is uint8[4])
                lines.append(f"        private final {java_type}[] {nested_field.name};")
            else:
                lines.append(f"        private final {java_type} {nested_field.name};")
        elif isinstance(nested_field, EnumField):
            # Enum field - use the enum's Java type (handles bitflags → int)
            java_type = nested_field.enum_def.java_type
            if nested_field.is_array():
                lines.append(f"        private final {java_type}[] {nested_field.name};")
            else:
                lines.append(f"        private final {java_type} {nested_field.name};")
        elif isinstance(nested_field, CompositeField):  # Nested composite
            nested_class_name = field_to_pascal_case(nested_field.name)
            if nested_field.array:
                lines.append(
                    f"        private final List<{nested_class_name}> {nested_field.name};"
                )
            else:
                lines.append(f"        private final {nested_class_name} {nested_field.name};")

    lines.append("")

    # Constructor
    params: list[str] = []
    for nested_field in field.fields:
        if isinstance(nested_field, PrimitiveField):
            java_type = _get_java_type(nested_field.type_name.value, type_registry)
            if nested_field.is_array():
                params.append(f"{java_type}[] {nested_field.name}")
            else:
                params.append(f"{java_type} {nested_field.name}")
        elif isinstance(nested_field, EnumField):
            java_type = nested_field.enum_def.java_type
            if nested_field.is_array():
                params.append(f"{java_type}[] {nested_field.name}")
            else:
                params.append(f"{java_type} {nested_field.name}")
        elif isinstance(nested_field, CompositeField):
            nested_class_name = field_to_pascal_case(nested_field.name)
            if nested_field.array:
                params.append(f"List<{nested_class_name}> {nested_field.name}")
            else:
                params.append(f"{nested_class_name} {nested_field.name}")

    param_str = ", ".join(params)
    lines.append(f"        public {class_name}({param_str}) {{")
    for nested_field in field.fields:
        lines.append(f"            this.{nested_field.name} = {nested_field.name};")
    lines.append("        }")
    lines.append("")

    # Getters
    for nested_field in field.fields:
        getter_name = _to_getter_name(nested_field.name)
        if isinstance(nested_field, PrimitiveField):
            java_type = _get_java_type(nested_field.type_name.value, type_registry)
            if nested_field.is_array():
                java_type = f"{java_type}[]"
        elif isinstance(nested_field, EnumField):
            enum_java_type = nested_field.enum_def.java_type
            java_type = f"{enum_java_type}[]" if nested_field.is_array() else enum_java_type
        elif isinstance(nested_field, CompositeField):
            nested_class_name = field_to_pascal_case(nested_field.name)
            java_type = f"List<{nested_class_name}>" if nested_field.array else nested_class_name
        else:
            raise TypeError(f"Unknown field type: {type(nested_field)}")

        lines.append(f"        public {java_type} {getter_name}() {{")
        lines.append(f"            return {nested_field.name};")
        lines.append("        }")
        lines.append("")

    lines.append("    }")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# IMPORT ANALYSIS HELPERS
# ============================================================================


def _needs_list_import(fields: Sequence[FieldBase]) -> bool:
    """Check if List import is needed.

    Since composite arrays now use T[] (aligned with C++ std::array),
    List is no longer needed for any message types.
    """
    # All arrays (primitive and composite) now use T[] - no List import needed
    return False


def _needs_constants_import(fields: Sequence[FieldBase], type_registry: TypeRegistry) -> bool:
    """Check if ProtocolConstants import is needed (any string field)."""
    for field in fields:
        if isinstance(field, PrimitiveField):
            if field.type_name.value == "string":
                return True
        elif isinstance(field, CompositeField) and _needs_constants_import(
            field.fields, type_registry
        ):
            # Check nested fields recursively
            return True
        # EnumField doesn't need constants import
    return False
