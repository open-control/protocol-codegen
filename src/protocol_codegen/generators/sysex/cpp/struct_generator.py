"""
C++ Struct Generator
Generates struct/*.hpp files from messages with Encoder calls.

This generator creates lightweight C++ structs that call Encoder functions
instead of duplicating encoding logic. This achieves -73% code reduction
while maintaining identical performance (compiler inlines everything).

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

# Import field classes for runtime isinstance checks
from protocol_codegen.core.field import CompositeField, EnumField, FieldBase, PrimitiveField
from protocol_codegen.generators.common.cpp.codec_utils import (
    get_cpp_type,
    get_decoder_call,
    get_encoder_call,
)
from protocol_codegen.generators.common.encoding import SysExEncodingStrategy
from protocol_codegen.generators.common.naming import (
    field_to_pascal_case,
    to_pascal_case,
)
from protocol_codegen.generators.common.payload_calculator import PayloadCalculator

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message


def generate_struct_hpp(
    message: Message,
    message_id: int,
    type_registry: TypeRegistry,
    output_path: Path,
    string_max_length: int,
    include_message_name: bool = False,
) -> str:
    """
    Generate C++ struct header for a message (supports composite fields).

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

    header = _generate_header(struct_name, description, fields, type_registry)

    # NEW: Generate composite structs FIRST (if any)
    composite_structs = _generate_composite_structs(fields, type_registry)

    struct_def = _generate_struct_definition(
        struct_name, message.name, pascal_name, message_id, fields, type_registry, include_message_name
    )
    encode_fn = _generate_encode_function(
        struct_name, pascal_name, fields, type_registry, string_max_length, include_message_name
    )
    decode_fn = _generate_decode_function(
        struct_name, fields, type_registry, string_max_length, include_message_name
    )

    footer = _generate_footer()

    # Insert composite structs BEFORE main message struct
    full_code = f"{header}\n{composite_structs}\n{struct_def}\n{encode_fn}\n{decode_fn}\n{footer}}};\n\n}}  // namespace Protocol\n"
    return full_code


def _analyze_includes_needed(
    fields: Sequence[FieldBase], type_registry: TypeRegistry
) -> tuple[bool, bool, bool, set[str]]:
    """
    Analyze fields to determine which standard includes are needed.

    Returns:
        Tuple of (needs_array, needs_string, needs_vector, enum_names)
    """
    needs_array = False
    needs_string = False
    needs_vector = False
    enum_names: set[str] = set()

    def check_field(field: FieldBase) -> None:
        nonlocal needs_array, needs_string, needs_vector

        if isinstance(field, EnumField):
            # Enum field - collect enum name for include
            enum_names.add(field.enum_def.name)
            if field.array:
                needs_array = True
        elif isinstance(field, PrimitiveField):
            # Check for string type
            if field.type_name.value == "string":
                needs_string = True
            # Check for array (fixed or dynamic)
            if field.array:
                if field.dynamic:
                    needs_vector = True
                else:
                    needs_array = True
        elif isinstance(field, CompositeField):
            # Composite field
            if field.array:
                needs_array = True
            # Recursively check nested fields
            for nested in field.fields:
                check_field(nested)

    for field in fields:
        check_field(field)

    return needs_array, needs_string, needs_vector, enum_names


def _generate_header(
    struct_name: str,
    description: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
) -> str:
    """Generate file header with conditional includes based on field analysis."""
    needs_array, needs_string, needs_vector, enum_names = _analyze_includes_needed(
        fields, type_registry
    )

    # Build conditional includes
    std_includes = ["#include <cstdint>", "#include <optional>"]
    if needs_array:
        std_includes.insert(0, "#include <array>")
    if needs_string:
        std_includes.append("#include <string>")
    if needs_vector:
        std_includes.append("#include <vector>")

    std_includes_str = "\n".join(std_includes)

    # Build enum includes
    enum_includes = ""
    if enum_names:
        enum_include_lines = [f'#include "../{name}.hpp"' for name in sorted(enum_names)]
        enum_includes = "\n" + "\n".join(enum_include_lines)

    return f"""/**
 * {struct_name}.hpp - Auto-generated Protocol Struct
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: types.yaml
 *
 * Description: {description}
 *
 * This struct uses encode/decode functions from Protocol namespace.
 * All encoding is 7-bit MIDI-safe. Performance is identical to inline
 * code due to static inline + compiler optimization.
 */

#pragma once

#include "../Encoder.hpp"
#include "../Decoder.hpp"
#include "../MessageID.hpp"
#include "../ProtocolConstants.hpp"{enum_includes}
{std_includes_str}

namespace Protocol {{

"""


def _generate_struct_definition(
    struct_name: str,
    message_name: str,  # SCREAMING_SNAKE_CASE name (e.g., "TRANSPORT_PLAY")
    pascal_name: str,  # PascalCase name (e.g., "TransportPlay") - used for MESSAGE_NAME
    message_id: int,  # Allocated ID (e.g., 0x40)
    fields: Sequence[FieldBase],  # Sequence of Field objects (primitive OR composite)
    type_registry: TypeRegistry,
    include_message_name: bool = False,
) -> str:
    """Generate struct definition with fields (supports composites)."""
    lines = [f"struct {struct_name} {{"]

    # Add static MESSAGE_ID constant
    lines.append("    // Auto-detected MessageID for protocol.send()")
    lines.append(f"    static constexpr MessageID MESSAGE_ID = MessageID::{message_name};")

    # Add static MESSAGE_NAME constant (for logging/debugging) - only if enabled
    if include_message_name:
        lines.append("")
        lines.append(f'    static constexpr const char* MESSAGE_NAME = "{pascal_name}";')

    lines.append("")

    # Add fields (use new helper that handles both primitive and composite)
    for field in fields:
        cpp_type = _get_cpp_type_for_field(field, type_registry)
        lines.append(f"    {cpp_type} {field.name};")

    lines.append("")
    return "\n".join(lines)


def _generate_encode_function(
    struct_name: str,
    pascal_name: str,  # PascalCase name for MESSAGE_NAME encoding
    fields: Sequence[FieldBase],  # Sequence of Field objects
    type_registry: TypeRegistry,
    string_max_length: int,
    include_message_name: bool = False,
) -> str:
    """Generate encode() function calling Encoder."""
    # Calculate max and min payload sizes using PayloadCalculator
    name_prefix_size = (1 + len(pascal_name)) if include_message_name else 0
    calculator = PayloadCalculator(SysExEncodingStrategy(), type_registry)
    max_size = calculator.calculate_max_payload_size(
        fields, string_max_length, name_prefix_size
    )
    min_size = calculator.calculate_min_payload_size(
        fields, string_max_length, name_prefix_size
    )

    lines = [
        "    /**",
        "     * Maximum payload size in bytes (7-bit encoded)",
        "     */",
        f"    static constexpr uint16_t MAX_PAYLOAD_SIZE = {max_size};",
        "",
        "    /**",
        "     * Minimum payload size in bytes (with empty strings)",
        "     */",
        f"    static constexpr uint16_t MIN_PAYLOAD_SIZE = {min_size};",
        "",
    ]

    # Simplified encode for empty messages
    if not fields:
        if include_message_name:
            # Include MESSAGE_NAME in payload
            lines.extend(
                [
                    "    /**",
                    "     * Encode struct to MIDI-safe bytes (empty message with name prefix)",
                    "     * @return Number of bytes written",
                    "     */",
                    "    uint16_t encode(uint8_t* buffer, uint16_t bufferSize) const {",
                    "        if (bufferSize < MAX_PAYLOAD_SIZE) return 0;",
                    "        uint8_t* ptr = buffer;",
                    "        encodeUint8(ptr, static_cast<uint8_t>(strlen(MESSAGE_NAME)));",
                    "        for (size_t i = 0; i < strlen(MESSAGE_NAME); ++i) {",
                    "            *ptr++ = static_cast<uint8_t>(MESSAGE_NAME[i]);",
                    "        }",
                    "        return ptr - buffer;",
                    "    }",
                    "",
                ]
            )
        else:
            # No MESSAGE_NAME - empty payload
            lines.extend(
                [
                    "    /**",
                    "     * Encode struct to MIDI-safe bytes (empty message)",
                    "     * @return Always 0 (no payload)",
                    "     */",
                    "    uint16_t encode(uint8_t*, uint16_t) const { return 0; }",
                    "",
                ]
            )
        return "\n".join(lines)

    # Standard encode for messages with fields
    lines.extend(
        [
            "    /**",
            "     * Encode struct to MIDI-safe bytes",
            "     *",
            "     * @param buffer Output buffer (must have >= MAX_PAYLOAD_SIZE bytes)",
            "     * @param bufferSize Size of output buffer",
            "     * @return Number of bytes written, or 0 if buffer too small",
            "     */",
            "    uint16_t encode(uint8_t* buffer, uint16_t bufferSize) const {",
            "        if (bufferSize < MAX_PAYLOAD_SIZE) return 0;",
            "",
            "        uint8_t* ptr = buffer;",
            "",
        ]
    )

    # Conditionally encode MESSAGE_NAME
    if include_message_name:
        lines.extend(
            [
                "        // Encode MESSAGE_NAME prefix",
                "        encodeUint8(ptr, static_cast<uint8_t>(strlen(MESSAGE_NAME)));",
                "        for (size_t i = 0; i < strlen(MESSAGE_NAME); ++i) {",
                "            *ptr++ = static_cast<uint8_t>(MESSAGE_NAME[i]);",
                "        }",
                "",
            ]
        )

    # Add encode calls for each field
    for field in fields:
        if isinstance(field, EnumField):
            # Enum field - encode as uint8 with cast
            if field.is_array():
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
                lines.append("            encodeUint8(ptr, static_cast<uint8_t>(item));")
                lines.append("        }")
            else:
                lines.append(f"        encodeUint8(ptr, static_cast<uint8_t>({field.name}));")
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            if field.is_array():
                # Primitive array (e.g., string[16])
                # ALWAYS encode count prefix (same as composite arrays for consistency)
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
                encoder_call = get_encoder_call("item", field_type_name, type_registry)
                lines.append(f"            {encoder_call}")
                lines.append("        }")
            else:
                # Scalar primitive
                encoder_call = get_encoder_call(field.name, field_type_name, type_registry)
                lines.append(f"        {encoder_call}")
        elif isinstance(field, CompositeField):
            # Composite - encode array of structs
            if field.array:
                # Encode array count first
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                # Loop over array and encode each struct's fields
                lines.append(f"        for (const auto& item : {field.name}) {{")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        # Nested enum field
                        if nested_field.is_array():
                            lines.append(
                                f"            encodeUint8(ptr, item.{nested_field.name}.size());"
                            )
                            lines.append(
                                f"            for (const auto& e : item.{nested_field.name}) {{"
                            )
                            lines.append("                encodeUint8(ptr, static_cast<uint8_t>(e));")
                            lines.append("            }")
                        else:
                            lines.append(
                                f"            encodeUint8(ptr, static_cast<uint8_t>(item.{nested_field.name}));"
                            )
                    elif isinstance(nested_field, PrimitiveField):
                        if nested_field.is_array():
                            # Nested array of primitives - encode count for dynamic arrays
                            lines.append(
                                f"            encodeUint8(ptr, item.{nested_field.name}.size());"
                            )
                            lines.append(
                                f"            for (const auto& type : item.{nested_field.name}) {{"
                            )
                            encoder_call = get_encoder_call(
                                "type", nested_field.type_name.value, type_registry
                            )
                            lines.append(f"                {encoder_call}")
                            lines.append("            }")
                        else:
                            # Nested scalar primitive
                            encoder_call = get_encoder_call(
                                f"item.{nested_field.name}",
                                nested_field.type_name.value,
                                type_registry,
                            )
                            lines.append(f"            {encoder_call}")
                lines.append("        }")
            else:
                # Single composite struct (not array)
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        lines.append(
                            f"        encodeUint8(ptr, static_cast<uint8_t>({field.name}.{nested_field.name}));"
                        )
                    elif isinstance(nested_field, PrimitiveField):
                        encoder_call = get_encoder_call(
                            f"{field.name}.{nested_field.name}",
                            nested_field.type_name.value,
                            type_registry,
                        )
                        lines.append(f"        {encoder_call}")

    # Return encoded bytes count
    lines.append("")
    lines.append("        return ptr - buffer;")
    lines.extend(["    }", ""])

    return "\n".join(lines)


def _generate_decode_function(
    struct_name: str,
    fields: Sequence[FieldBase],  # Sequence of Field objects
    type_registry: TypeRegistry,
    string_max_length: int,
    include_message_name: bool = False,
) -> str:
    """Generate static decode() function calling Decoder."""
    # Simplified decode for empty messages
    if not fields:
        if include_message_name:
            # Skip MESSAGE_NAME prefix
            return f"""    /**
     * Decode struct from MIDI-safe bytes (empty message with name prefix)
     * @return Always returns empty struct after skipping name prefix
     */
    static std::optional<{struct_name}> decode(const uint8_t* data, uint16_t len) {{
        if (len < MIN_PAYLOAD_SIZE) return std::nullopt;
        const uint8_t* ptr = data;
        size_t remaining = len;
        // Skip MESSAGE_NAME prefix
        uint8_t nameLen;
        if (!decodeUint8(ptr, remaining, nameLen)) return std::nullopt;
        ptr += nameLen;
        remaining -= nameLen;
        return {struct_name}{{}};
    }}
"""
        else:
            # No MESSAGE_NAME - just return empty struct
            return f"""    /**
     * Decode struct from MIDI-safe bytes (empty message)
     * @return Always returns empty struct
     */
    static std::optional<{struct_name}> decode(const uint8_t*, uint16_t) {{
        return {struct_name}{{}};
    }}
"""

    # Standard decode for messages with fields
    lines = [
        "    /**",
        "     * Decode struct from MIDI-safe bytes",
        "     *",
        "     * @param data Input buffer with encoded data",
        "     * @param len Length of input buffer",
        "     * @return Decoded struct, or std::nullopt if invalid/insufficient data",
        "     */",
        f"    static std::optional<{struct_name}> decode(",
        "        const uint8_t* data, uint16_t len) {",
        "",
        "        if (len < MIN_PAYLOAD_SIZE) return std::nullopt;",
        "",
        "        const uint8_t* ptr = data;",
        "        size_t remaining = len;",
        "",
    ]

    # Conditionally skip MESSAGE_NAME prefix
    if include_message_name:
        lines.extend(
            [
                "        // Skip MESSAGE_NAME prefix",
                "        uint8_t nameLen;",
                "        if (!decodeUint8(ptr, remaining, nameLen)) return std::nullopt;",
                "        ptr += nameLen;",
                "        remaining -= nameLen;",
                "",
            ]
        )

    lines.append("        // Decode fields")

    # Add decode calls for each field
    field_vars: list[str] = []
    for field in fields:
        if isinstance(field, EnumField):
            # Enum field - decode as uint8 and cast
            cpp_type = field.enum_def.cpp_type
            if field.is_array():
                var_name = f"{field.name}_data"
                array_type = _get_cpp_type_for_field(field, type_registry)
                lines.append(f"        {array_type} {var_name};")
                lines.append(f"        uint8_t count_{field.name};")
                lines.append(
                    f"        if (!decodeUint8(ptr, remaining, count_{field.name})) return std::nullopt;"
                )
                lines.append(
                    f"        for (uint8_t i = 0; i < count_{field.name} && i < {field.array}; ++i) {{"
                )
                lines.append("            uint8_t temp_raw;")
                lines.append(
                    "            if (!decodeUint8(ptr, remaining, temp_raw)) return std::nullopt;"
                )
                lines.append(f"            {var_name}[i] = static_cast<{cpp_type}>(temp_raw);")
                lines.append("        }")
                field_vars.append(var_name)
            else:
                # Scalar enum
                lines.append(f"        uint8_t {field.name}_raw;")
                lines.append(
                    f"        if (!decodeUint8(ptr, remaining, {field.name}_raw)) return std::nullopt;"
                )
                lines.append(
                    f"        {cpp_type} {field.name} = static_cast<{cpp_type}>({field.name}_raw);"
                )
                field_vars.append(field.name)
        elif isinstance(field, PrimitiveField):
            field_type_name = field.type_name.value
            if field.is_array():
                # Primitive array (e.g., string[16])
                cpp_type = _get_cpp_type_for_field(field, type_registry)
                var_name = f"{field.name}_data"
                lines.append(f"        {cpp_type} {var_name};")

                # For std::vector (dynamic), read count from message; for std::array (fixed), use known size
                if field.dynamic:
                    # Dynamic vector: read count, decode into temp var and push_back
                    lines.append(f"        uint8_t count_{field.name};")
                    lines.append(
                        f"        if (!decodeUint8(ptr, remaining, count_{field.name})) return std::nullopt;"
                    )
                    lines.append(
                        f"        for (uint8_t i = 0; i < count_{field.name} && i < {field.array}; ++i) {{"
                    )
                    base_cpp_type = get_cpp_type(field_type_name, type_registry)
                    lines.append(f"            {base_cpp_type} temp_item;")
                    decoder_call = get_decoder_call(
                        "temp_item", field_type_name, type_registry, direct_target="temp_item"
                    )
                    lines.append(f"            {decoder_call}")
                    lines.append(f"            {var_name}.push_back(temp_item);")
                    lines.append("        }")
                else:
                    # Fixed array: decode directly by index, using known array size
                    lines.append(f"        for (uint8_t i = 0; i < {field.array}; ++i) {{")
                    decoder_call = get_decoder_call(
                        "temp_item", field_type_name, type_registry, direct_target=f"{var_name}[i]"
                    )
                    lines.append(f"            {decoder_call}")
                    lines.append("        }")

                field_vars.append(var_name)
            else:
                # Scalar primitive
                decoder_call = get_decoder_call(field.name, field_type_name, type_registry)
                lines.append(f"        {decoder_call}")
                field_vars.append(field.name)
        elif isinstance(field, CompositeField):
            # Composite - decode array of structs
            var_name = f"{field.name}_data"
            if field.array:
                # Decode array count (BUG FIX: use output parameter syntax)
                lines.append(f"        uint8_t count_{field.name};")
                lines.append(
                    f"        if (!decodeUint8(ptr, remaining, count_{field.name})) return std::nullopt;"
                )
                # std::array type (fixed size, but we fill based on count)
                cpp_type = _get_cpp_type_for_field(field, type_registry)
                lines.append(f"        {cpp_type} {var_name};")
                # Use PascalCase struct name for item type (BUG FIX #4)
                item_struct_name = field_to_pascal_case(field.name)
                lines.append(
                    f"        for (uint8_t i = 0; i < count_{field.name} && i < {field.array}; ++i) {{"
                )
                lines.append(f"            {item_struct_name} item;")
                # Decode each field of the struct
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        # Nested enum field
                        nested_cpp_type = nested_field.enum_def.cpp_type
                        if nested_field.is_array():
                            lines.append(f"            uint8_t count_{nested_field.name};")
                            lines.append(
                                f"            if (!decodeUint8(ptr, remaining, count_{nested_field.name})) return std::nullopt;"
                            )
                            lines.append(
                                f"            for (uint8_t j = 0; j < count_{nested_field.name} && j < {nested_field.array}; ++j) {{"
                            )
                            lines.append("                uint8_t temp_raw;")
                            lines.append(
                                "                if (!decodeUint8(ptr, remaining, temp_raw)) return std::nullopt;"
                            )
                            lines.append(
                                f"                item.{nested_field.name}[j] = static_cast<{nested_cpp_type}>(temp_raw);"
                            )
                            lines.append("            }")
                        else:
                            lines.append(f"            uint8_t {nested_field.name}_raw;")
                            lines.append(
                                f"            if (!decodeUint8(ptr, remaining, {nested_field.name}_raw)) return std::nullopt;"
                            )
                            lines.append(
                                f"            item.{nested_field.name} = static_cast<{nested_cpp_type}>({nested_field.name}_raw);"
                            )
                    elif isinstance(nested_field, PrimitiveField):
                        if nested_field.is_array():
                            # Nested array of primitives - decode count for dynamic arrays
                            lines.append(f"            uint8_t count_{nested_field.name};")
                            lines.append(
                                f"            if (!decodeUint8(ptr, remaining, count_{nested_field.name})) return std::nullopt;"
                            )

                            # For std::vector, we need to use push_back instead of direct indexing
                            if nested_field.dynamic:
                                # Dynamic vector: decode into temp var and push_back
                                lines.append(
                                    f"            for (uint8_t j = 0; j < count_{nested_field.name} && j < {nested_field.array}; ++j) {{"
                                )
                                cpp_type = get_cpp_type(
                                    nested_field.type_name.value, type_registry
                                )
                                lines.append(
                                    f"                {cpp_type} temp_{nested_field.name};"
                                )
                                decoder_call = get_decoder_call(
                                    f"temp_{nested_field.name}",
                                    nested_field.type_name.value,
                                    type_registry,
                                    direct_target=f"temp_{nested_field.name}",
                                )
                                lines.append(f"                {decoder_call}")
                                lines.append(
                                    f"                item.{nested_field.name}.push_back(temp_{nested_field.name});"
                                )
                                lines.append("            }")
                            else:
                                # Fixed array: decode directly by index
                                lines.append(
                                    f"            for (uint8_t j = 0; j < count_{nested_field.name} && j < {nested_field.array}; ++j) {{"
                                )
                                direct_target = f"item.{nested_field.name}[j]"
                                decoder_call = get_decoder_call(
                                    f"item_{nested_field.name}_j",
                                    nested_field.type_name.value,
                                    type_registry,
                                    direct_target=direct_target,
                                )
                                lines.append(f"                {decoder_call}")
                                lines.append("            }")
                        else:
                            # Nested scalar primitive
                            # OPTION B: Write directly to item struct member
                            direct_target = f"item.{nested_field.name}"
                            decoder_call = get_decoder_call(
                                f"item_{nested_field.name}",  # Unused when direct_target set
                                nested_field.type_name.value,
                                type_registry,
                                direct_target=direct_target,
                            )
                            lines.append(f"            {decoder_call}")
                lines.append(
                    f"            {var_name}[i] = item;"
                )  # Use array index instead of push_back
                lines.append("        }")
            else:
                # Single composite struct (not array)
                # BUG FIX #2: Use capitalized struct type name instead of field name
                struct_type = field.name[0].upper() + field.name[1:]  # camelCase → PascalCase
                lines.append(f"        {struct_type} {var_name};")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        # Nested enum field
                        nested_cpp_type = nested_field.enum_def.cpp_type
                        lines.append(f"        uint8_t {nested_field.name}_raw;")
                        lines.append(
                            f"        if (!decodeUint8(ptr, remaining, {nested_field.name}_raw)) return std::nullopt;"
                        )
                        lines.append(
                            f"        {var_name}.{nested_field.name} = static_cast<{nested_cpp_type}>({nested_field.name}_raw);"
                        )
                    elif isinstance(nested_field, PrimitiveField):
                        # OPTION B: Write directly to struct member (no temporary variable)
                        direct_target = f"{var_name}.{nested_field.name}"
                        decoder_call = get_decoder_call(
                            f"{field.name}_{nested_field.name}",  # Unused when direct_target set
                            nested_field.type_name.value,
                            type_registry,
                            direct_target=direct_target,
                        )
                        lines.append(f"        {decoder_call}")
            field_vars.append(var_name)

    # Construct and return struct
    # Primitives use output parameters (no dereference needed)
    # Composites return optional (need dereference)
    field_values: list[str] = []
    for i, field in enumerate(fields):
        var = field_vars[i]
        if field.is_primitive() and not field.is_array():
            field_values.append(var)  # Scalar primitive - output parameter, use directly
        else:
            field_values.append(var)  # Array or composite - use _data variable

    field_list = ", ".join(field_values)
    lines.extend(["", f"        return {struct_name}{{{field_list}}};", "    }", ""])

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate struct closing brace."""
    return ""  # Closed in main function


# ============================================================================
# COMPOSITE FIELD SUPPORT (Phase 2)
# ============================================================================


def _generate_composite_structs(
    fields: Sequence[FieldBase], type_registry: TypeRegistry, depth: int = 0
) -> str:
    """
    Recursively generate all composite struct definitions from fields.
    Returns empty string if no composites found.
    """
    if depth > 3:
        return ""  # Safety: max recursion depth

    structs: list[str] = []
    for field in fields:
        if field.is_composite():
            assert isinstance(field, CompositeField)
            # Generate nested composites first (depth-first)
            nested = _generate_composite_structs(field.fields, type_registry, depth + 1)
            if nested:
                structs.append(nested)

            # Generate this composite struct
            struct_code = _generate_single_composite_struct(field, type_registry)
            structs.append(struct_code)

    return "\n".join(structs)


def _generate_single_composite_struct(field: CompositeField, type_registry: TypeRegistry) -> str:
    """
    Generate a single composite struct definition with include guards.

    BUG FIX #1: Wrap struct in #ifndef guard to prevent redefinition
    when multiple messages use the same composite type.
    """
    # BUG FIX #4: Convert camelCase to PascalCase (pageInfo → PageInfo, not Pageinfo)
    struct_name = field_to_pascal_case(field.name)

    # Generate include guard macro (PROTOCOL_<STRUCT_NAME>_HPP)
    guard_macro = f"PROTOCOL_{struct_name.upper()}_STRUCT"

    lines = [f"#ifndef {guard_macro}", f"#define {guard_macro}", "", f"struct {struct_name} {{"]

    # Add member fields
    for nested_field in field.fields:
        if isinstance(nested_field, EnumField):
            # Enum field - use the enum's C++ type
            enum_type = nested_field.enum_def.cpp_type
            if nested_field.array:
                lines.append(f"    std::array<{enum_type}, {nested_field.array}> {nested_field.name};")
            else:
                lines.append(f"    {enum_type} {nested_field.name};")
        elif isinstance(nested_field, PrimitiveField):
            # Get base C++ type without array wrapper
            base_type = get_cpp_type(nested_field.type_name.value, type_registry)
            if nested_field.array:
                # Use std::vector for dynamic arrays, std::array for fixed
                if nested_field.dynamic:
                    lines.append(f"    std::vector<{base_type}> {nested_field.name};")
                else:
                    lines.append(
                        f"    std::array<{base_type}, {nested_field.array}> {nested_field.name};"
                    )
            else:
                lines.append(f"    {base_type} {nested_field.name};")
        elif isinstance(nested_field, CompositeField):
            # Nested composite
            nested_struct_name = field_to_pascal_case(nested_field.name)
            if nested_field.array:
                lines.append(
                    f"    std::array<{nested_struct_name}, {nested_field.array}> {nested_field.name};"
                )
            else:
                lines.append(f"    {nested_struct_name} {nested_field.name};")

    lines.append("};")
    lines.append("")
    lines.append(f"#endif // {guard_macro}")
    lines.append("")
    return "\n".join(lines)


def _get_cpp_type_for_field(field: FieldBase, type_registry: TypeRegistry) -> str:
    """Get C++ type for a field (handles primitive, composite, and enum)."""
    if isinstance(field, EnumField):
        # Enum field - use the enum's C++ type
        cpp_type = field.enum_def.cpp_type
        if field.array:
            return f"std::array<{cpp_type}, {field.array}>"
        return cpp_type
    elif isinstance(field, PrimitiveField):
        base_type = get_cpp_type(field.type_name.value, type_registry)
        if field.array:
            # Use std::vector for dynamic arrays, std::array for fixed
            if field.dynamic:
                return f"std::vector<{base_type}>"
            else:
                return f"std::array<{base_type}, {field.array}>"
        return base_type
    else:  # Composite
        assert isinstance(field, CompositeField)
        # BUG FIX #4: Convert camelCase to PascalCase
        struct_name = field_to_pascal_case(field.name)
        if field.array:
            return f"std::array<{struct_name}, {field.array}>"
        return struct_name
