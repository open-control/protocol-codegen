"""
Java Constants Generator for Serial8 Protocol
Generates ProtocolConstants.java from Serial8Config.

Key Features:
- public static final for constants
- Message structure offsets
- Encoding limits (max string length, max array items, etc.)
- No SysEx framing (handled by COBS at bridge layer)

Generated Output:
- ProtocolConstants.java (~40 lines)
- Package: Configurable via plugin_paths
- All constants are public static final
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from pathlib import Path


class StructureConfig(TypedDict, total=False):
    """Message structure configuration."""

    message_type_offset: int
    from_host_offset: int
    payload_offset: int


class LimitsConfig(TypedDict, total=False):
    """Protocol encoding limits."""

    string_max_length: int
    array_max_items: int
    max_payload_size: int
    max_message_size: int


class ProtocolConfig(TypedDict, total=False):
    """Protocol configuration structure for Serial8."""

    structure: StructureConfig
    limits: LimitsConfig


def generate_constants_java(
    protocol_config: ProtocolConfig, output_path: Path, package: str
) -> str:
    """
    Generate ProtocolConstants.java for Serial8 protocol.

    Args:
        protocol_config: Dict with structure and limits config
        output_path: Path where ProtocolConstants.java will be written
        package: Java package name (e.g., 'protocol' or 'com.example.protocol')

    Returns:
        Generated Java code as string
    """
    header = _generate_header(package)
    structure = _generate_structure_constants(protocol_config.get("structure", {}))
    limits = _generate_limits(protocol_config.get("limits", {}))
    footer = _generate_footer()

    return f"{header}\n{structure}\n{limits}\n{footer}"


def _generate_header(package: str) -> str:
    """Generate file header with package and class declaration."""
    return f"""package {package};

/**
 * ProtocolConstants - Protocol Configuration Constants (Serial8)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: Serial8Config
 *
 * This class contains all protocol constants including message structure
 * offsets and encoding limits for 8-bit binary protocol.
 *
 * Note: Framing (COBS) is handled by the bridge layer, not the codec.
 *
 * All constants are public static final (compile-time constants).
 */
public final class ProtocolConstants {{

    // Private constructor prevents instantiation (utility class)
    private ProtocolConstants() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // MESSAGE STRUCTURE CONSTANTS
    // ============================================================================
"""


def _generate_structure_constants(structure_config: StructureConfig) -> str:
    """Generate message structure constants."""
    lines: list[str] = []

    type_offset: int = structure_config.get("message_type_offset", 0)
    from_host_offset: int = structure_config.get("from_host_offset", 1)
    payload_offset: int = structure_config.get("payload_offset", 2)

    lines.append("    /** Position of MessageID byte in message */")
    lines.append(f"    public static final int MESSAGE_TYPE_OFFSET = {type_offset};")
    lines.append("")
    lines.append("    /** Position of fromHost flag in message */")
    lines.append(f"    public static final int FROM_HOST_OFFSET = {from_host_offset};")
    lines.append("")
    lines.append("    /** Start of payload data in message */")
    lines.append(f"    public static final int PAYLOAD_OFFSET = {payload_offset};")
    lines.append("")
    lines.append("    /** Minimum valid message length */")
    lines.append(f"    public static final int MIN_MESSAGE_LENGTH = {payload_offset};")

    return "\n".join(lines)


def _generate_limits(limits_config: LimitsConfig) -> str:
    """Generate encoding limits constants."""
    lines: list[str] = [
        "",
        "    // ============================================================================",
        "    // ENCODING LIMITS",
        "    // ============================================================================",
        "",
    ]

    # String limits (8-bit protocol max = 255)
    string_max: int = limits_config.get("string_max_length", 255)
    lines.append("    /** Maximum characters per string field (8-bit length) */")
    lines.append(f"    public static final int STRING_MAX_LENGTH = {string_max};")
    lines.append("")

    # Array limits (8-bit protocol max = 255)
    array_max: int = limits_config.get("array_max_items", 255)
    lines.append("    /** Maximum items per array field (8-bit count) */")
    lines.append(f"    public static final int ARRAY_MAX_ITEMS = {array_max};")
    lines.append("")

    # Payload limits
    max_payload: int = limits_config.get("max_payload_size", 4096)
    max_message: int = limits_config.get("max_message_size", 4096)
    lines.append("    /** Maximum payload bytes */")
    lines.append(f"    public static final int MAX_PAYLOAD_SIZE = {max_payload};")
    lines.append("")
    lines.append("    /** Maximum total message bytes */")
    lines.append(f"    public static final int MAX_MESSAGE_SIZE = {max_message};")

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate class closing."""
    return """

}  // class ProtocolConstants
"""
