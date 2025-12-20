"""
C++ Constants Generator for Serial8 Protocol
Generates ProtocolConstants.hpp from Serial8Config.

Key Features:
- Constexpr for compile-time constants
- Message structure offsets
- Encoding limits (max string length, max array items, etc.)
- No SysEx framing bytes (handled by COBS at bridge layer)

Generated Output:
- ProtocolConstants.hpp (~40 lines)
- Namespace: Protocol
- All constexpr (zero runtime cost)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


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


def generate_constants_hpp(
    protocol_config: ProtocolConfig, type_registry: TypeRegistry, output_path: Path
) -> str:
    """
    Generate ProtocolConstants.hpp for Serial8 protocol.

    Args:
        protocol_config: Dict with structure and limits config
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where ProtocolConstants.hpp will be written

    Returns:
        Generated C++ code as string
    """
    uint8_cpp = type_registry.get("uint8").cpp_type
    uint16_cpp = type_registry.get("uint16").cpp_type

    if uint8_cpp is None or uint16_cpp is None:
        raise ValueError("Missing C++ type mappings for uint8 or uint16")

    header = _generate_header()
    structure = _generate_structure_constants(protocol_config.get("structure", {}), uint8_cpp)
    limits = _generate_limits(protocol_config.get("limits", {}), uint8_cpp, uint16_cpp)
    footer = _generate_footer()

    return f"{header}\n{structure}\n{limits}\n{footer}"


def _generate_header() -> str:
    """Generate file header."""
    return """/**
 * ProtocolConstants.hpp - Protocol Configuration Constants (Serial8)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: Serial8Config
 *
 * This file contains all protocol constants including message structure
 * offsets and encoding limits for 8-bit binary protocol.
 *
 * Note: Framing (COBS) is handled by the bridge layer, not the codec.
 *
 * All constants are constexpr (compile-time, zero runtime cost).
 */

#pragma once

#include <cstdint>

namespace Protocol {

// ============================================================================
// MESSAGE STRUCTURE CONSTANTS
// ============================================================================
"""


def _generate_structure_constants(structure_config: StructureConfig, uint8_type: str) -> str:
    """Generate message structure constants."""
    lines: list[str] = []

    type_offset: int = structure_config.get("message_type_offset", 0)
    from_host_offset: int = structure_config.get("from_host_offset", 1)
    payload_offset: int = structure_config.get("payload_offset", 2)

    lines.append(
        f"constexpr {uint8_type} MESSAGE_TYPE_OFFSET = {type_offset};  // Position of MessageID byte"
    )
    lines.append(
        f"constexpr {uint8_type} FROM_HOST_OFFSET = {from_host_offset};      // Position of fromHost flag"
    )
    lines.append(
        f"constexpr {uint8_type} PAYLOAD_OFFSET = {payload_offset};          // Start of payload data"
    )
    lines.append(
        f"constexpr {uint8_type} MIN_MESSAGE_LENGTH = {payload_offset};  // Minimum valid message size"
    )

    return "\n".join(lines)


def _generate_limits(limits_config: LimitsConfig, uint8_type: str, uint16_type: str) -> str:
    """Generate encoding limits constants."""
    lines: list[str] = [
        "",
        "// ============================================================================",
        "// ENCODING LIMITS",
        "// ============================================================================",
        "",
    ]

    # String limits (8-bit protocol max = 255)
    string_max: int = limits_config.get("string_max_length", 255)
    lines.append(
        f"constexpr {uint8_type} STRING_MAX_LENGTH = {string_max};  // Max chars per string (8-bit length)"
    )

    # Array limits (8-bit protocol max = 255)
    array_max: int = limits_config.get("array_max_items", 255)
    lines.append(
        f"constexpr {uint8_type} ARRAY_MAX_ITEMS = {array_max};    // Max items per array (8-bit count)"
    )

    # Payload limits
    max_payload: int = limits_config.get("max_payload_size", 4096)
    max_message: int = limits_config.get("max_message_size", 4096)
    lines.append(
        f"constexpr {uint16_type} MAX_PAYLOAD_SIZE = {max_payload};  // Max payload bytes"
    )
    lines.append(
        f"constexpr {uint16_type} MAX_MESSAGE_SIZE = {max_message};  // Max total message bytes"
    )

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate namespace closing."""
    return """

}  // namespace Protocol
"""
