"""
ProtocolMethods.hpp Generator

Generates explicit API methods based on message direction and intent.
- TO_HOST messages: generate send methods (Controller sends to Host)
- TO_CONTROLLER messages: generate callback declarations (Controller receives from Host)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.naming import (
    message_name_to_callback_name,
    message_name_to_method_name,
    should_exclude_field,
    to_pascal_case,
)

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.field import FieldBase, PrimitiveField
    from protocol_codegen.core.message import Message


# Type mapping from protocol types to C++ types
# Note: Type enum values are lowercase (e.g., 'bool', 'uint8')
_CPP_TYPE_MAP = {
    "bool": "bool",
    "uint8": "uint8_t",
    "int8": "int8_t",
    "uint16": "uint16_t",
    "int16": "int16_t",
    "uint32": "uint32_t",
    "int32": "int32_t",
    "float32": "float",
    "string": "const std::string&",
    "norm8": "uint8_t",
    "norm16": "uint16_t",
}


def _get_cpp_type(field: FieldBase) -> str:
    """Get C++ type for a field."""
    if field.is_composite():
        # For composite fields, use the struct name
        struct_name = to_pascal_case(field.name)
        if field.is_array():
            return f"const std::array<{struct_name}, {field.array}>&"
        return f"const {struct_name}&"

    # Primitive field
    pfield: PrimitiveField = field  # type: ignore[assignment]
    base_type = _CPP_TYPE_MAP.get(pfield.type_name.value, "auto")

    if field.is_array():
        if pfield.dynamic:
            return f"const std::vector<{base_type}>&"
        return f"const std::array<{base_type}, {field.array}>&"

    return base_type


def _get_field_arg_name(field: FieldBase) -> str:
    """Get argument name for a field (camelCase)."""
    # Convert snake_case to camelCase if needed
    name = field.name
    if "_" in name:
        parts = name.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])
    return name


def _generate_method_params(fields: list[FieldBase]) -> str:
    """Generate method parameters from fields."""
    params = []
    for field in fields:
        if should_exclude_field(field.name):
            continue
        cpp_type = _get_cpp_type(field)
        arg_name = _get_field_arg_name(field)
        params.append(f"{cpp_type} {arg_name}")
    return ", ".join(params)


def _generate_struct_args(fields: list[FieldBase]) -> str:
    """Generate struct initializer arguments from fields."""
    args = []
    for field in fields:
        if should_exclude_field(field.name):
            continue
        args.append(_get_field_arg_name(field))
    return ", ".join(args)


def generate_protocol_methods_hpp(
    messages: list[Message],
    output_path: Path,
) -> str:
    """
    Generate ProtocolMethods.hpp with explicit API methods.

    For TO_HOST messages: generates send methods (Controller -> Host)
    For TO_CONTROLLER messages: generates callback declarations (Host -> Controller)

    Args:
        messages: List of message definitions (only new-style with direction)
        output_path: Where to write ProtocolMethods.hpp

    Returns:
        Generated C++ code
    """
    to_host_methods: list[str] = []
    to_controller_callbacks: list[str] = []

    for msg in messages:
        if msg.is_legacy() or msg.deprecated:
            continue

        struct_name = to_pascal_case(msg.name) + "Message"

        if msg.is_to_host():
            # Controller sends to Host -> generate send method
            method_name = message_name_to_method_name(msg.name)
            params = _generate_method_params(list(msg.fields))
            args = _generate_struct_args(list(msg.fields))

            if params:
                to_host_methods.append(f"    void {method_name}({params}) {{")
                to_host_methods.append(f"        send({struct_name}{{{args}}});")
                to_host_methods.append("    }")
            else:
                to_host_methods.append(f"    void {method_name}() {{")
                to_host_methods.append(f"        send({struct_name}{{}});")
                to_host_methods.append("    }")
            to_host_methods.append("")

        elif msg.is_to_controller():
            # Host sends to Controller -> generate callback declaration
            callback_name = message_name_to_callback_name(msg.name)
            to_controller_callbacks.append(
                f"    std::function<void(const {struct_name}&)> {callback_name};"
            )

    to_host_str = "\n".join(to_host_methods) if to_host_methods else "    // No TO_HOST messages"
    to_controller_str = (
        "\n".join(to_controller_callbacks)
        if to_controller_callbacks
        else "    // No TO_CONTROLLER messages"
    )

    return f"""/**
 * ProtocolMethods.hpp - Explicit Protocol API
 *
 * AUTO-GENERATED - DO NOT EDIT
 *
 * This file provides explicit API methods instead of generic send<T>().
 * Include this file in your Protocol class definition.
 *
 * Pattern:
 *   TO_HOST messages (Controller -> Host): void methodName(params)
 *   TO_CONTROLLER messages (Host -> Controller): std::function<void(...)> onMethodName
 */

#pragma once

#include "MessageStructure.hpp"
#include <functional>
#include <string>
#include <array>
#include <vector>

namespace Protocol {{

/**
 * Explicit protocol methods (include in Protocol class)
 */
class ProtocolMethods {{
public:
    // =========================================================================
    // COMMANDS (Controller -> Host)
    // =========================================================================

{to_host_str}
    // =========================================================================
    // NOTIFICATIONS (Host -> Controller) - Callbacks
    // =========================================================================

{to_controller_str}

protected:
    ProtocolMethods() = default;
    virtual ~ProtocolMethods() = default;

    // Subclass must implement send
    template <typename T>
    void send(const T& msg);
}};

}}  // namespace Protocol
"""
