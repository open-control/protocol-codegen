"""
ProtocolMethods.java Generator

Generates explicit API methods based on message direction and intent.
- TO_HOST messages: generate callback declarations (Host receives from Controller)
- TO_CONTROLLER messages: generate send methods (Host sends to Controller)
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


# Type mapping from protocol types to Java types
# Note: Type enum values are lowercase (e.g., 'bool', 'uint8')
_JAVA_TYPE_MAP = {
    "bool": "boolean",
    "uint8": "int",
    "int8": "int",
    "uint16": "int",
    "int16": "int",
    "uint32": "int",
    "int32": "int",
    "float32": "float",
    "string": "String",
    "norm8": "int",
    "norm16": "int",
}


def _field_to_pascal_case(field_name: str) -> str:
    """
    Convert camelCase field name to PascalCase class name.

    This matches the struct generator's naming for inner classes.

    Examples:
        pageInfo → PageInfo
        remoteControls → RemoteControls
        deviceName → DeviceName
    """
    if not field_name:
        return field_name
    return field_name[0].upper() + field_name[1:]


def _get_java_type(field: FieldBase, message_struct_name: str) -> str:
    """
    Get Java type for a field.

    Args:
        field: The field to get the type for
        message_struct_name: The parent message struct name (e.g., "DeviceChangeMessage")
                            Used to qualify composite types as inner classes.
    """
    if field.is_composite():
        # Composite fields are inner classes of the message struct
        # e.g., DeviceChangeMessage.PageInfo, DeviceChangeMessage.RemoteControls
        inner_class_name = _field_to_pascal_case(field.name)
        qualified_type = f"{message_struct_name}.{inner_class_name}"
        if field.is_array():
            return f"{qualified_type}[]"
        return qualified_type

    # Primitive field
    pfield: PrimitiveField = field  # type: ignore[assignment]
    base_type = _JAVA_TYPE_MAP.get(pfield.type_name.value, "Object")

    if field.is_array():
        return f"{base_type}[]"

    return base_type


def _get_field_arg_name(field: FieldBase) -> str:
    """Get argument name for a field (camelCase)."""
    name = field.name
    if "_" in name:
        parts = name.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])
    return name


def _generate_method_params(fields: list[FieldBase], message_struct_name: str) -> str:
    """Generate method parameters from fields."""
    params = []
    for field in fields:
        if should_exclude_field(field.name):
            continue
        java_type = _get_java_type(field, message_struct_name)
        arg_name = _get_field_arg_name(field)
        params.append(f"{java_type} {arg_name}")
    return ", ".join(params)


def _generate_struct_args(fields: list[FieldBase]) -> str:
    """Generate struct constructor arguments from fields."""
    args = []
    for field in fields:
        if should_exclude_field(field.name):
            continue
        args.append(_get_field_arg_name(field))
    return ", ".join(args)


def generate_protocol_methods_java(
    messages: list[Message],
    output_path: Path,
    package: str,
) -> str:
    """
    Generate ProtocolMethods.java with explicit API methods.

    For TO_HOST messages: generates callback declarations (Host receives from Controller)
    For TO_CONTROLLER messages: generates send methods (Host sends to Controller)

    Args:
        messages: List of message definitions (only new-style with direction)
        output_path: Where to write ProtocolMethods.java
        package: Java package name

    Returns:
        Generated Java code
    """
    to_host_callbacks: list[str] = []
    to_controller_methods: list[str] = []

    for msg in messages:
        if msg.is_legacy() or msg.deprecated:
            continue

        struct_name = to_pascal_case(msg.name) + "Message"

        if msg.is_to_host():
            # Controller sends to Host -> generate callback declaration
            callback_name = message_name_to_callback_name(msg.name)
            to_host_callbacks.append(
                f"    public Consumer<{struct_name}> {callback_name} = null;"
            )

        elif msg.is_to_controller():
            # Host sends to Controller -> generate send method
            method_name = message_name_to_method_name(msg.name)
            params = _generate_method_params(list(msg.fields), struct_name)
            args = _generate_struct_args(list(msg.fields))

            if params:
                to_controller_methods.append(f"    public void {method_name}({params}) {{")
                to_controller_methods.append(f"        send(new {struct_name}({args}));")
                to_controller_methods.append("    }")
            else:
                to_controller_methods.append(f"    public void {method_name}() {{")
                to_controller_methods.append(f"        send(new {struct_name}());")
                to_controller_methods.append("    }")
            to_controller_methods.append("")

    to_host_str = (
        "\n".join(to_host_callbacks) if to_host_callbacks else "    // No TO_HOST messages"
    )
    to_controller_str = (
        "\n".join(to_controller_methods)
        if to_controller_methods
        else "    // No TO_CONTROLLER messages"
    )

    return f"""/**
 * ProtocolMethods.java - Explicit Protocol API
 *
 * AUTO-GENERATED - DO NOT EDIT
 *
 * This class provides explicit API methods instead of generic send().
 * Extend this class or include its methods in your Protocol class.
 *
 * Pattern:
 *   TO_HOST messages (Controller -> Host): Consumer<T> onMethodName
 *   TO_CONTROLLER messages (Host -> Controller): void methodName(params)
 */

package {package};

import java.util.function.Consumer;
import {package}.struct.*;

/**
 * Explicit protocol methods base class
 */
public abstract class ProtocolMethods {{

    // =========================================================================
    // COMMANDS (Controller -> Host) - Callbacks
    // =========================================================================

{to_host_str}

    // =========================================================================
    // NOTIFICATIONS (Host -> Controller) - Send Methods
    // =========================================================================

{to_controller_str}
    // =========================================================================
    // Abstract send method (implemented by subclass)
    // =========================================================================

    protected abstract void send(Object message);
}}
"""
