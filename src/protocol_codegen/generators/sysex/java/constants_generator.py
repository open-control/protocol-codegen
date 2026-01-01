"""
Java Constants Generator
Generates ProtocolConstants.java from protocol_config.yaml.

This generator extracts SysEx framing constants and protocol limits
from the YAML configuration and generates Java constants.

Key Features:
- public static final for constants
- SysEx framing (manufacturer_id, device_id, etc.)
- Message structure offsets
- Encoding limits (max string length, max array items, etc.)

Generated Output:
- ProtocolConstants.java (~50-100 lines)
- Package: Configurable via plugin_paths
- All constants are public static final
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from pathlib import Path


class SysExConfig(TypedDict, total=False):
    """SysEx framing configuration"""

    start: int
    end: int
    manufacturer_id: int
    device_id: int
    min_message_length: int
    message_type_offset: int
    payload_offset: int


class LimitsConfig(TypedDict, total=False):
    """Protocol encoding limits"""

    string_max_length: int
    array_max_items: int
    max_payload_size: int
    max_message_size: int


class ProtocolConfig(TypedDict, total=False):
    """Protocol configuration structure from protocol_config.yaml"""

    sysex: SysExConfig
    limits: LimitsConfig


def generate_constants_java(
    protocol_config: ProtocolConfig, output_path: Path, package: str
) -> str:
    """
    Generate ProtocolConstants.java from protocol_config.yaml.

    Args:
        protocol_config: Dict loaded from protocol_config.yaml
        output_path: Path where ProtocolConstants.java will be written
        package: Java package name (e.g., 'protocol' or 'com.example.protocol')

    Returns:
        Generated Java code as string

    Example:
        >>> with open('protocol_config.yaml') as f:
        ...     config = yaml.safe_load(f)
        >>> code = generate_constants_java(config, Path('ProtocolConstants.java'), 'protocol')
    """
    header = _generate_header(package)
    sysex_constants = _generate_sysex_constants(protocol_config.get("sysex", {}))
    limits = _generate_limits(protocol_config.get("limits", {}))
    footer = _generate_footer()

    full_code = f"{header}\n{sysex_constants}\n{limits}\n{footer}"
    return full_code


def _generate_header(package: str) -> str:
    """Generate file header with package and class declaration."""
    return f"""package {package};

/**
 * ProtocolConstants - Protocol Configuration Constants
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: protocol_config.yaml
 *
 * This class contains all protocol constants including SysEx framing,
 * message structure offsets, and encoding limits.
 *
 * All constants are public static final (compile-time constants).
 */
public final class ProtocolConstants {{

    // Private constructor prevents instantiation (utility class)
    private ProtocolConstants() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // SYSEX FRAMING CONSTANTS
    // ============================================================================
"""


def _generate_sysex_constants(sysex_config: SysExConfig) -> str:
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


def _generate_limits(limits_config: LimitsConfig) -> str:
    """Generate encoding limits constants."""
    if not limits_config:
        return ""

    lines: list[str] = [
        "",
        "    // ============================================================================",
        "    // ENCODING LIMITS",
        "    // ============================================================================",
        "",
    ]

    # String limits (7-bit protocol max = 127)
    string_max: int = limits_config.get("string_max_length", 127)
    lines.append("    /** Maximum characters per string field (7-bit encoding) */")
    lines.append(f"    public static final int STRING_MAX_LENGTH = {string_max};")
    lines.append("")

    # Array limits (7-bit protocol max = 127)
    array_max: int = limits_config.get("array_max_items", 127)
    lines.append("    /** Maximum items per array field (7-bit count) */")
    lines.append(f"    public static final int ARRAY_MAX_ITEMS = {array_max};")
    lines.append("")

    # Payload limits
    max_payload: int = limits_config.get("max_payload_size", 256)
    max_message: int = limits_config.get("max_message_size", 261)
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
