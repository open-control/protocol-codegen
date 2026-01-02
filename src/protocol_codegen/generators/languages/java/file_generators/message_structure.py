"""
MessageStructure.java Generator

Generates umbrella class that imports and re-exports all message structs.
This mirrors C++ MessageStructure.hpp pattern - single import point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_message_structure_java(
    messages: list[Message],
    output_path: Path,
    base_package: str = "protocol",
    struct_package: str = "protocol.struct",
) -> str:
    """
    Generate MessageStructure.java umbrella class.

    This class is placed in the base package and imports all message
    classes from the struct package, mirroring C++ MessageStructure.hpp.

    Args:
        messages: List of message definitions
        output_path: Where to write MessageStructure.java
        base_package: Base Java package (e.g., 'protocol')
        struct_package: Struct Java package (e.g., 'protocol.struct')

    Returns:
        Generated Java code
    """
    # Generate imports for all message structs
    imports: list[str] = []
    class_refs: list[str] = []

    for message in messages:
        # Convert SCREAMING_SNAKE_CASE to PascalCase
        pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
        class_name = f"{pascal_name}Message"

        imports.append(f"import {struct_package}.{class_name};")
        class_refs.append(f"    /** @see {class_name} */")
        class_refs.append(
            f"    public static final Class<{class_name}> {message.name} = {class_name}.class;"
        )

    imports_str = "\n".join(imports)
    class_refs_str = "\n".join(class_refs)

    code = f"""package {base_package};

{imports_str}

/**
 * MessageStructure - Umbrella class for all protocol messages
 *
 * AUTO-GENERATED - DO NOT EDIT
 *
 * This class imports all message struct definitions from the struct package.
 * Use this single import in your code instead of importing individual structs.
 *
 * Usage:
 *   import {base_package}.MessageStructure;
 *
 *   TransportPlayMessage msg = new TransportPlayMessage(true);
 *   msg.encode(buffer, 0);
 */
public final class MessageStructure {{

    private MessageStructure() {{
        // Prevent instantiation
    }}

    // ============================================================================
    // Message Class References
    // ============================================================================

{class_refs_str}

}}
"""

    return code
