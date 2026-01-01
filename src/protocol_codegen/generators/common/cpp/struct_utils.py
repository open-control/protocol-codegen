"""
Common C++ Struct Generator Utilities.

Shared utilities for generating C++ struct headers across protocols (Serial8, SysEx).
Protocol-specific behavior is controlled by EncodingStrategy and config parameters.

Key Differences:
- Serial8: always_encode_array_count=True, needs_cstring=True, encoding="8-bit binary"
- SysEx: always_encode_array_count=False, needs_cstring=False, encoding="7-bit MIDI-safe"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.core.field import CompositeField, EnumField, FieldBase, PrimitiveField
from protocol_codegen.generators.common.cpp.codec_utils import (
    get_cpp_type,
    get_decoder_call,
    get_encoder_call,
)
from protocol_codegen.generators.common.encoding import EncodingStrategy
from protocol_codegen.generators.common.naming import field_to_pascal_case
from protocol_codegen.generators.common.payload_calculator import PayloadCalculator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from protocol_codegen.core.loader import TypeRegistry


def analyze_includes_needed(
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
            enum_names.add(field.enum_def.name)
            if field.array:
                needs_array = True
        elif isinstance(field, PrimitiveField):
            if field.type_name.value == "string":
                needs_string = True
            if field.array:
                if field.dynamic:
                    needs_vector = True
                else:
                    needs_array = True
        elif isinstance(field, CompositeField):
            if field.array:
                needs_array = True
            for nested in field.fields:
                check_field(nested)

    for field in fields:
        check_field(field)

    return needs_array, needs_string, needs_vector, enum_names


def generate_header(
    struct_name: str,
    description: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    encoding_description: str,
    needs_cstring: bool = False,
) -> str:
    """
    Generate file header with conditional includes based on field analysis.

    Args:
        struct_name: Name of the struct (e.g., "TransportPlayMessage")
        description: Description for the header comment
        fields: Message fields
        type_registry: TypeRegistry for resolving field types
        encoding_description: Encoding description for comment (e.g., "8-bit binary (Serial8)")
        needs_cstring: Whether to include <cstring> (Serial8 needs it)
    """
    needs_array, needs_string, needs_vector, enum_names = analyze_includes_needed(
        fields, type_registry
    )

    # Build conditional includes
    std_includes = ["#include <cstdint>"]
    if needs_cstring:
        std_includes.append("#include <cstring>")
    std_includes.append("#include <optional>")
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
 * All encoding is {encoding_description}. Performance is identical to inline
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


def generate_struct_definition(
    struct_name: str,
    message_name: str,
    pascal_name: str,
    message_id: int,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    include_message_name: bool = True,
) -> str:
    """Generate struct definition with fields (supports composites)."""
    lines = [f"struct {struct_name} {{"]

    # Add static MESSAGE_ID constant
    lines.append("    // Auto-detected MessageID for protocol.send()")
    lines.append(f"    static constexpr MessageID MESSAGE_ID = MessageID::{message_name};")
    lines.append("")

    # Add static MESSAGE_NAME constant (for logging/debugging) - only if enabled
    if include_message_name:
        lines.append("    // Message name for logging (encoded in payload)")
        lines.append(f'    static constexpr const char* MESSAGE_NAME = "{pascal_name}";')
        lines.append("")

    # Add fields
    for field in fields:
        cpp_type = get_cpp_type_for_field(field, type_registry)
        lines.append(f"    {cpp_type} {field.name};")

    lines.append("")
    return "\n".join(lines)


def generate_encode_function(
    struct_name: str,
    pascal_name: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    string_max_length: int,
    strategy: EncodingStrategy,
    encoding_description: str,
    include_message_name: bool = True,
) -> str:
    """
    Generate encode() function calling Encoder.

    Args:
        struct_name: Name of the struct
        pascal_name: PascalCase name for MESSAGE_NAME encoding
        fields: Message fields
        type_registry: TypeRegistry for resolving field types
        string_max_length: Maximum string length from config
        strategy: EncodingStrategy for payload calculations
        encoding_description: Encoding description for comments (e.g., "8-bit", "7-bit")
        include_message_name: Whether to include MESSAGE_NAME in payload
    """
    # Calculate max and min payload sizes using PayloadCalculator
    name_prefix_size = (1 + len(pascal_name)) if include_message_name else 0
    calculator = PayloadCalculator(strategy, type_registry)
    max_size = calculator.calculate_max_payload_size(
        fields, string_max_length, name_prefix_size
    )
    min_size = calculator.calculate_min_payload_size(
        fields, string_max_length, name_prefix_size
    )

    lines = [
        "    /**",
        f"     * Maximum payload size in bytes ({encoding_description} encoded)",
        "     */",
        f"    static constexpr uint16_t MAX_PAYLOAD_SIZE = {max_size};",
        "",
        "    /**",
        "     * Minimum payload size in bytes (with empty strings)",
        "     */",
        f"    static constexpr uint16_t MIN_PAYLOAD_SIZE = {min_size};",
        "",
    ]

    # Encode for empty messages
    if not fields:
        if include_message_name:
            lines.extend(
                [
                    "    /**",
                    "     * Encode struct to MIDI-safe bytes (message name only, no fields)",
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
                    "        // Encode message name (length-prefixed string for bridge logging)",
                    "        encodeUint8(ptr, static_cast<uint8_t>(strlen(MESSAGE_NAME)));",
                    "        for (size_t i = 0; i < strlen(MESSAGE_NAME); ++i) {",
                    "            *ptr++ = static_cast<uint8_t>(MESSAGE_NAME[i]);",
                    "        }",
                    "",
                    "        return ptr - buffer;",
                    "    }",
                    "",
                ]
            )
        else:
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
                "        // Encode message name (length-prefixed string for bridge logging)",
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
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
                encoder_call = get_encoder_call("item", field_type_name, type_registry)
                lines.append(f"            {encoder_call}")
                lines.append("        }")
            else:
                encoder_call = get_encoder_call(field.name, field_type_name, type_registry)
                lines.append(f"        {encoder_call}")
        elif isinstance(field, CompositeField):
            if field.array:
                lines.append(f"        encodeUint8(ptr, {field.name}.size());")
                lines.append(f"        for (const auto& item : {field.name}) {{")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
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
                            encoder_call = get_encoder_call(
                                f"item.{nested_field.name}",
                                nested_field.type_name.value,
                                type_registry,
                            )
                            lines.append(f"            {encoder_call}")
                lines.append("        }")
            else:
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

    lines.append("")
    lines.append("        return ptr - buffer;")
    lines.extend(["    }", ""])

    return "\n".join(lines)


def generate_decode_function(
    struct_name: str,
    fields: Sequence[FieldBase],
    type_registry: TypeRegistry,
    string_max_length: int,
    include_message_name: bool = True,
    always_encode_array_count: bool = True,
) -> str:
    """
    Generate static decode() function calling Decoder.

    Args:
        struct_name: Name of the struct
        fields: Message fields
        type_registry: TypeRegistry for resolving field types
        string_max_length: Maximum string length from config
        include_message_name: Whether MESSAGE_NAME is in payload
        always_encode_array_count: If True (Serial8), always read count from message.
                                   If False (SysEx), fixed arrays use known size.
    """
    # Decode for empty messages
    if not fields:
        if include_message_name:
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
            cpp_type = field.enum_def.cpp_type
            if field.is_array():
                var_name = f"{field.name}_data"
                array_type = get_cpp_type_for_field(field, type_registry)
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
                cpp_type = get_cpp_type_for_field(field, type_registry)
                var_name = f"{field.name}_data"
                lines.append(f"        {cpp_type} {var_name};")

                if field.dynamic or always_encode_array_count:
                    # Read count from message
                    lines.append(f"        uint8_t count_{field.name};")
                    lines.append(
                        f"        if (!decodeUint8(ptr, remaining, count_{field.name})) return std::nullopt;"
                    )
                    if field.dynamic:
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
                        lines.append(
                            f"        for (uint8_t i = 0; i < count_{field.name} && i < {field.array}; ++i) {{"
                        )
                        decoder_call = get_decoder_call(
                            "temp_item", field_type_name, type_registry, direct_target=f"{var_name}[i]"
                        )
                        lines.append(f"            {decoder_call}")
                        lines.append("        }")
                else:
                    # Fixed array without count (SysEx mode)
                    lines.append(f"        for (uint8_t i = 0; i < {field.array}; ++i) {{")
                    decoder_call = get_decoder_call(
                        "temp_item", field_type_name, type_registry, direct_target=f"{var_name}[i]"
                    )
                    lines.append(f"            {decoder_call}")
                    lines.append("        }")

                field_vars.append(var_name)
            else:
                decoder_call = get_decoder_call(field.name, field_type_name, type_registry)
                lines.append(f"        {decoder_call}")
                field_vars.append(field.name)
        elif isinstance(field, CompositeField):
            var_name = f"{field.name}_data"
            if field.array:
                lines.append(f"        uint8_t count_{field.name};")
                lines.append(
                    f"        if (!decodeUint8(ptr, remaining, count_{field.name})) return std::nullopt;"
                )
                cpp_type = get_cpp_type_for_field(field, type_registry)
                lines.append(f"        {cpp_type} {var_name};")
                item_struct_name = field_to_pascal_case(field.name)
                lines.append(
                    f"        for (uint8_t i = 0; i < count_{field.name} && i < {field.array}; ++i) {{"
                )
                lines.append(f"            {item_struct_name} item;")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
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
                            lines.append(f"            uint8_t count_{nested_field.name};")
                            lines.append(
                                f"            if (!decodeUint8(ptr, remaining, count_{nested_field.name})) return std::nullopt;"
                            )
                            if nested_field.dynamic:
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
                            direct_target = f"item.{nested_field.name}"
                            decoder_call = get_decoder_call(
                                f"item_{nested_field.name}",
                                nested_field.type_name.value,
                                type_registry,
                                direct_target=direct_target,
                            )
                            lines.append(f"            {decoder_call}")
                lines.append(f"            {var_name}[i] = item;")
                lines.append("        }")
            else:
                struct_type = field.name[0].upper() + field.name[1:]
                lines.append(f"        {struct_type} {var_name};")
                for nested_field in field.fields:
                    if isinstance(nested_field, EnumField):
                        nested_cpp_type = nested_field.enum_def.cpp_type
                        lines.append(f"        uint8_t {nested_field.name}_raw;")
                        lines.append(
                            f"        if (!decodeUint8(ptr, remaining, {nested_field.name}_raw)) return std::nullopt;"
                        )
                        lines.append(
                            f"        {var_name}.{nested_field.name} = static_cast<{nested_cpp_type}>({nested_field.name}_raw);"
                        )
                    elif isinstance(nested_field, PrimitiveField):
                        direct_target = f"{var_name}.{nested_field.name}"
                        decoder_call = get_decoder_call(
                            f"{field.name}_{nested_field.name}",
                            nested_field.type_name.value,
                            type_registry,
                            direct_target=direct_target,
                        )
                        lines.append(f"        {decoder_call}")
            field_vars.append(var_name)

    # Construct and return struct
    field_values: list[str] = []
    for i, field in enumerate(fields):
        var = field_vars[i]
        if field.is_primitive() and not field.is_array():
            field_values.append(var)
        else:
            field_values.append(var)

    field_list = ", ".join(field_values)
    lines.extend(["", f"        return {struct_name}{{{field_list}}};", "    }", ""])

    return "\n".join(lines)


def generate_footer() -> str:
    """Generate struct closing brace."""
    return ""


def generate_composite_structs(
    fields: Sequence[FieldBase], type_registry: TypeRegistry, depth: int = 0
) -> str:
    """
    Recursively generate all composite struct definitions from fields.
    Returns empty string if no composites found.
    """
    if depth > 3:
        return ""

    structs: list[str] = []
    for field in fields:
        if field.is_composite():
            assert isinstance(field, CompositeField)
            nested = generate_composite_structs(field.fields, type_registry, depth + 1)
            if nested:
                structs.append(nested)
            struct_code = generate_single_composite_struct(field, type_registry)
            structs.append(struct_code)

    return "\n".join(structs)


def generate_single_composite_struct(field: CompositeField, type_registry: TypeRegistry) -> str:
    """
    Generate a single composite struct definition with include guards.
    """
    struct_name = field_to_pascal_case(field.name)
    guard_macro = f"PROTOCOL_{struct_name.upper()}_STRUCT"

    lines = [f"#ifndef {guard_macro}", f"#define {guard_macro}", "", f"struct {struct_name} {{"]

    for nested_field in field.fields:
        if isinstance(nested_field, PrimitiveField):
            base_type = get_cpp_type(nested_field.type_name.value, type_registry)
            if nested_field.array:
                if nested_field.dynamic:
                    lines.append(f"    std::vector<{base_type}> {nested_field.name};")
                else:
                    lines.append(
                        f"    std::array<{base_type}, {nested_field.array}> {nested_field.name};"
                    )
            else:
                lines.append(f"    {base_type} {nested_field.name};")
        elif isinstance(nested_field, EnumField):
            enum_type = nested_field.enum_def.cpp_type
            if nested_field.array:
                lines.append(f"    std::array<{enum_type}, {nested_field.array}> {nested_field.name};")
            else:
                lines.append(f"    {enum_type} {nested_field.name};")
        elif isinstance(nested_field, CompositeField):
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


def get_cpp_type_for_field(field: FieldBase, type_registry: TypeRegistry) -> str:
    """Get C++ type for a field (handles primitive, composite, and enum)."""
    if isinstance(field, EnumField):
        cpp_type = field.enum_def.cpp_type
        if field.array:
            return f"std::array<{cpp_type}, {field.array}>"
        return cpp_type
    elif isinstance(field, PrimitiveField):
        base_type = get_cpp_type(field.type_name.value, type_registry)
        if field.array:
            if field.dynamic:
                return f"std::vector<{base_type}>"
            else:
                return f"std::array<{base_type}, {field.array}>"
        return base_type
    else:
        assert isinstance(field, CompositeField)
        struct_name = field_to_pascal_case(field.name)
        if field.array:
            return f"std::array<{struct_name}, {field.array}>"
        return struct_name
