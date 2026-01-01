"""
C++ Constants Generator (Unified)
Generates ProtocolConstants.hpp for both Serial8 and SysEx protocols.

This unified generator handles both protocol types by detecting the config format:
- If 'sysex' key is present → SysEx protocol (7-bit MIDI framing)
- If 'structure' key is present → Serial8 protocol (8-bit binary)

Key Features:
- Constexpr for compile-time constants
- Protocol-specific header comments
- Message structure offsets
- Encoding limits (max string length, max array items, etc.)
- Uses builtin_types.yaml for type consistency (SSOT)

Generated Output:
- ProtocolConstants.hpp (~50-100 lines depending on protocol)
- Namespace: Protocol
- All constexpr (zero runtime cost)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.config import (
    LimitsConfig,
    ProtocolConfig,
    StructureConfig,
    SysExFramingConfig,
)

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def generate_constants_hpp(
    protocol_config: ProtocolConfig, type_registry: TypeRegistry, output_path: Path
) -> str:
    """
    Generate ProtocolConstants.hpp from protocol configuration.

    Automatically detects protocol type from config format:
    - 'sysex' key → SysEx protocol (7-bit MIDI framing)
    - 'structure' key → Serial8 protocol (8-bit binary)

    Args:
        protocol_config: Protocol configuration dict
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where ProtocolConstants.hpp will be written

    Returns:
        Generated C++ code as string
    """
    # Extract C++ types from builtin_types.yaml (SSOT)
    uint8_cpp = type_registry.get("uint8").cpp_type
    uint16_cpp = type_registry.get("uint16").cpp_type

    if uint8_cpp is None or uint16_cpp is None:
        raise ValueError("Missing C++ type mappings for uint8 or uint16 in builtin_types.yaml")

    # Detect protocol type and generate appropriate sections
    is_sysex = "sysex" in protocol_config
    protocol_name = "SysEx" if is_sysex else "Serial8"

    header = _generate_header(protocol_name, is_sysex)

    if is_sysex:
        protocol_section = _generate_sysex_constants(
            protocol_config.get("sysex", {}), uint8_cpp
        )
    else:
        protocol_section = _generate_structure_constants(
            protocol_config.get("structure", {}), uint8_cpp
        )

    limits = _generate_limits(protocol_config.get("limits", {}), uint8_cpp, uint16_cpp, is_sysex)
    footer = _generate_footer()

    return f"{header}\n{protocol_section}\n{limits}\n{footer}"


# ─────────────────────────────────────────────────────────────────────────────
# Private Generators
# ─────────────────────────────────────────────────────────────────────────────


def _generate_header(protocol_name: str, is_sysex: bool) -> str:
    """Generate file header with protocol-specific comments."""
    if is_sysex:
        description = """This file contains all protocol constants including SysEx framing,
 * message structure offsets, and encoding limits."""
        section_title = "SYSEX FRAMING CONSTANTS"
    else:
        description = """This file contains all protocol constants including message structure
 * offsets and encoding limits for 8-bit binary protocol.
 *
 * Note: Framing (COBS) is handled by the bridge layer, not the codec."""
        section_title = "MESSAGE STRUCTURE CONSTANTS"

    return f"""/**
 * ProtocolConstants.hpp - Protocol Configuration Constants ({protocol_name})
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: {protocol_name}Config
 *
 * {description}
 *
 * All constants are constexpr (compile-time, zero runtime cost).
 */

#pragma once

#include <cstdint>

namespace Protocol {{

// ============================================================================
// {section_title}
// ============================================================================
"""


def _generate_structure_constants(structure_config: StructureConfig, uint8_type: str) -> str:
    """Generate message structure constants for Serial8 protocol."""
    lines: list[str] = []

    type_offset: int = structure_config.get("message_type_offset", 0)
    payload_offset: int = structure_config.get("payload_offset", 1)

    lines.append(
        f"constexpr {uint8_type} MESSAGE_TYPE_OFFSET = {type_offset};  // Position of MessageID byte"
    )
    lines.append(
        f"constexpr {uint8_type} PAYLOAD_OFFSET = {payload_offset};          // Start of payload data"
    )
    lines.append(
        f"constexpr {uint8_type} MIN_MESSAGE_LENGTH = {payload_offset};  // Minimum valid message size"
    )

    return "\n".join(lines)


def _generate_sysex_constants(sysex_config: SysExFramingConfig, uint8_type: str) -> str:
    """Generate SysEx framing constants."""
    if not sysex_config:
        return "// No SysEx config found\n"

    lines: list[str] = []

    # Message delimiters
    start: int = sysex_config.get("start", 0xF0)
    end: int = sysex_config.get("end", 0xF7)
    lines.append(f"constexpr {uint8_type} SYSEX_START = {start:#04x};  // SysEx start byte")
    lines.append(f"constexpr {uint8_type} SYSEX_END = {end:#04x};    // SysEx end byte")
    lines.append("")

    # Protocol identifiers
    manufacturer_id: int = sysex_config.get("manufacturer_id", 0x7F)
    device_id: int = sysex_config.get("device_id", 0x01)
    lines.append(
        f"constexpr {uint8_type} MANUFACTURER_ID = {manufacturer_id:#04x};  // MIDI manufacturer ID"
    )
    lines.append(
        f"constexpr {uint8_type} DEVICE_ID = {device_id:#04x};        // Device identifier"
    )
    lines.append("")

    # Message structure
    min_length: int = sysex_config.get("min_message_length", 5)
    type_offset: int = sysex_config.get("message_type_offset", 3)
    payload_offset: int = sysex_config.get("payload_offset", 4)
    lines.append(
        f"constexpr {uint8_type} MIN_MESSAGE_LENGTH = {min_length};  // Minimum valid SysEx message"
    )
    lines.append(
        f"constexpr {uint8_type} MESSAGE_TYPE_OFFSET = {type_offset};  // Position of MessageID byte"
    )
    lines.append(
        f"constexpr {uint8_type} PAYLOAD_OFFSET = {payload_offset};      // Start of payload data"
    )

    return "\n".join(lines)


def _generate_limits(
    limits_config: LimitsConfig, uint8_type: str, uint16_type: str, is_sysex: bool
) -> str:
    """Generate encoding limits constants."""
    lines: list[str] = [
        "",
        "// ============================================================================",
        "// ENCODING LIMITS",
        "// ============================================================================",
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
    lines.append(
        f"constexpr {uint8_type} STRING_MAX_LENGTH = {string_max};  // Max chars per string ({encoding_comment})"
    )

    # Array limits
    array_max: int = limits_config.get("array_max_items", default_array_max)
    lines.append(
        f"constexpr {uint8_type} ARRAY_MAX_ITEMS = {array_max};    // Max items per array ({encoding_comment[0:5]} count)"
    )

    # Payload limits
    max_payload: int = limits_config.get("max_payload_size", default_max_payload)
    max_message: int = limits_config.get("max_message_size", default_max_message)
    lines.append(f"constexpr {uint16_type} MAX_PAYLOAD_SIZE = {max_payload};  // Max payload bytes")
    lines.append(
        f"constexpr {uint16_type} MAX_MESSAGE_SIZE = {max_message};  // Max total message bytes"
    )

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate namespace closing."""
    return """

}  // namespace Protocol
"""
