"""
Java Constants Generator (Unified)
Generates ProtocolConstants.java for both Binary and SysEx protocols.

This unified generator handles both protocol types by detecting the config format:
- If 'sysex' key is present → SysEx protocol (7-bit MIDI framing)
- If 'structure' key is present → Binary protocol (8-bit binary)

Key Features:
- public static final for constants
- Protocol-specific header comments
- Message structure offsets
- Encoding limits (max string length, max array items, etc.)

Generated Output:
- ProtocolConstants.java (~50-100 lines depending on protocol)
- Package: Configurable via plugin_paths
- All constants are public static final
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.core.config import (
    LimitsConfig,
    ProtocolConfig,
    StructureConfig,
    SysExFramingConfig,
)

if TYPE_CHECKING:
    from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def generate_constants_java(
    protocol_config: ProtocolConfig, output_path: Path, package: str
) -> str:
    """
    Generate ProtocolConstants.java from protocol configuration.

    Automatically detects protocol type from config format:
    - 'sysex' key → SysEx protocol (7-bit MIDI framing)
    - 'structure' key → Binary protocol (8-bit binary)

    Args:
        protocol_config: Protocol configuration dict
        output_path: Path where ProtocolConstants.java will be written
        package: Java package name (e.g., 'protocol' or 'com.example.protocol')

    Returns:
        Generated Java code as string
    """
    # Detect protocol type and generate appropriate sections
    is_sysex = "sysex" in protocol_config
    protocol_name = "SysEx" if is_sysex else "Binary"

    header = _generate_header(package, protocol_name, is_sysex)

    if is_sysex:
        protocol_section = _generate_sysex_constants(protocol_config.get("sysex", {}))
    else:
        protocol_section = _generate_structure_constants(protocol_config.get("structure", {}))

    limits = _generate_limits(protocol_config.get("limits", {}), is_sysex)
    footer = _generate_footer()

    return f"{header}\n{protocol_section}\n{limits}\n{footer}"


# ─────────────────────────────────────────────────────────────────────────────
# Private Generators
# ─────────────────────────────────────────────────────────────────────────────


def _generate_header(package: str, protocol_name: str, is_sysex: bool) -> str:
    """Generate file header with package and class declaration."""
    if is_sysex:
        description = """This class contains all protocol constants including SysEx framing,
 * message structure offsets, and encoding limits."""
        section_title = "SYSEX FRAMING CONSTANTS"
    else:
        description = """This class contains all protocol constants including message structure
 * offsets and encoding limits for 8-bit binary protocol.
 *
 * Note: Framing (COBS) is handled by the bridge layer, not the codec."""
        section_title = "MESSAGE STRUCTURE CONSTANTS"

    return f"""package {package};

/**
 * ProtocolConstants - Protocol Configuration Constants ({protocol_name})
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: {protocol_name}Config
 *
 * {description}
 *
 * All constants are public static final (compile-time constants).
 */
public final class ProtocolConstants {{

    // Private constructor prevents instantiation (utility class)
    private ProtocolConstants() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // {section_title}
    // ============================================================================
"""


def _generate_structure_constants(structure_config: StructureConfig) -> str:
    """Generate message structure constants for Binary protocol."""
    lines: list[str] = []

    type_offset: int = structure_config.get("message_type_offset", 0)
    payload_offset: int = structure_config.get("payload_offset", 1)

    lines.append("    /** Position of MessageID byte in message */")
    lines.append(f"    public static final int MESSAGE_TYPE_OFFSET = {type_offset};")
    lines.append("")
    lines.append("    /** Start of payload data in message */")
    lines.append(f"    public static final int PAYLOAD_OFFSET = {payload_offset};")
    lines.append("")
    lines.append("    /** Minimum valid message length */")
    lines.append(f"    public static final int MIN_MESSAGE_LENGTH = {payload_offset};")

    return "\n".join(lines)


def _generate_sysex_constants(sysex_config: SysExFramingConfig) -> str:
    """Generate SysEx framing constants."""
    if not sysex_config:
        return "    // No SysEx config found\n"

    lines: list[str] = []

    # Message delimiters
    start: int = sysex_config.get("start", 0xF0)
    end: int = sysex_config.get("end", 0xF7)

    # Cast to byte for values > 127
    start_str: str = f"(byte) {start:#04x}" if start >= 0x80 else f"{start:#04x}"
    end_str: str = f"(byte) {end:#04x}" if end >= 0x80 else f"{end:#04x}"

    lines.append("    /** SysEx start byte */")
    lines.append(f"    public static final byte SYSEX_START = {start_str};")
    lines.append("")
    lines.append("    /** SysEx end byte */")
    lines.append(f"    public static final byte SYSEX_END = {end_str};")
    lines.append("")

    # Protocol identifiers
    manufacturer_id: int = sysex_config.get("manufacturer_id", 0x7F)
    device_id: int = sysex_config.get("device_id", 0x01)

    lines.append("    /** MIDI manufacturer ID */")
    lines.append(f"    public static final byte MANUFACTURER_ID = {manufacturer_id:#04x};")
    lines.append("")
    lines.append("    /** Device identifier */")
    lines.append(f"    public static final byte DEVICE_ID = {device_id:#04x};")
    lines.append("")

    # Message structure
    min_length: int = sysex_config.get("min_message_length", 5)
    type_offset: int = sysex_config.get("message_type_offset", 3)
    payload_offset: int = sysex_config.get("payload_offset", 4)

    lines.append("    /** Minimum valid SysEx message length */")
    lines.append(f"    public static final int MIN_MESSAGE_LENGTH = {min_length};")
    lines.append("")
    lines.append("    /** Position of MessageID byte in SysEx message */")
    lines.append(f"    public static final int MESSAGE_TYPE_OFFSET = {type_offset};")
    lines.append("")
    lines.append("    /** Start of payload data in SysEx message */")
    lines.append(f"    public static final int PAYLOAD_OFFSET = {payload_offset};")

    return "\n".join(lines)


def _generate_limits(limits_config: LimitsConfig, is_sysex: bool) -> str:
    """Generate encoding limits constants."""
    lines: list[str] = [
        "",
        "    // ============================================================================",
        "    // ENCODING LIMITS",
        "    // ============================================================================",
        "",
    ]

    # Default values depend on protocol (7-bit vs 8-bit)
    default_string_max = 127 if is_sysex else 255
    default_array_max = 127 if is_sysex else 255
    default_max_payload = 256 if is_sysex else 4096
    default_max_message = 261 if is_sysex else 4096
    encoding_comment = "7-bit encoding" if is_sysex else "8-bit length"

    # String limits
    string_max: int = limits_config.get("string_max_length", default_string_max)
    lines.append(f"    /** Maximum characters per string field ({encoding_comment}) */")
    lines.append(f"    public static final int STRING_MAX_LENGTH = {string_max};")
    lines.append("")

    # Array limits
    array_max: int = limits_config.get("array_max_items", default_array_max)
    count_comment = "7-bit count" if is_sysex else "8-bit count"
    lines.append(f"    /** Maximum items per array field ({count_comment}) */")
    lines.append(f"    public static final int ARRAY_MAX_ITEMS = {array_max};")
    lines.append("")

    # Payload limits
    max_payload: int = limits_config.get("max_payload_size", default_max_payload)
    max_message: int = limits_config.get("max_message_size", default_max_message)
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
