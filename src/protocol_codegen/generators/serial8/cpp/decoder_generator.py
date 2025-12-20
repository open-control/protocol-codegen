"""
C++ Decoder Generator for Serial8 Protocol
Generates Decoder.hpp with 8-bit binary decoding functions.

This generator creates static inline decode functions for all builtin
types. Uses full 8-bit byte range for maximum efficiency.

Key Features:
- Direct 8-bit decoding (no 7-bit constraint)
- Little-endian byte order for multi-byte types
- Static inline functions (zero runtime overhead)
- bool success return pattern (no optional overhead)

Generated Output:
- Decoder.hpp (~150 lines)
- Namespace: Protocol
- All functions: static inline (header-only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import AtomicType, TypeRegistry


def generate_decoder_hpp(type_registry: TypeRegistry, output_path: Path) -> str:
    """
    Generate Decoder.hpp with 8-bit decode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Decoder.hpp will be written

    Returns:
        Generated C++ code as string
    """
    builtin_types: dict[str, AtomicType] = {
        name: atomic_type
        for name, atomic_type in type_registry.types.items()
        if atomic_type.is_builtin
    }

    header = _generate_header(builtin_types)
    decoders = _generate_decoders(builtin_types)
    footer = _generate_footer()

    return f"{header}\n{decoders}\n{footer}"


def _generate_header(builtin_types: dict[str, AtomicType]) -> str:
    """Generate file header with includes and namespace."""
    type_list = ", ".join(builtin_types.keys())

    return f"""/**
 * Decoder.hpp - 8-bit Binary Decoder (Serial8 Protocol)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: builtin_types.yaml
 *
 * This file provides static inline decode functions for all builtin
 * primitive types. Decodes 8-bit binary bytes to native types.
 *
 * Supported types: {type_list}
 *
 * Decoding Strategy:
 * - Direct byte reads (no 7-bit constraint)
 * - Little-endian for multi-byte integers
 * - IEEE 754 for floats
 * - 8-bit length prefix for strings/arrays
 *
 * Performance:
 * - Static inline = zero runtime overhead
 * - Compiler optimizes away function calls
 * - More efficient than 7-bit decoding
 *
 * Companion file: Encoder.hpp
 */

#pragma once

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>

namespace Protocol {{

// ============================================================================
// DECODE FUNCTIONS (8-bit binary bytes -> Type)
// ============================================================================
// Returns bool success, writes decoded value to output parameter
// Output parameter pattern minimizes memory footprint
// Returns false if insufficient data
"""


def _generate_decoders(builtin_types: dict[str, AtomicType]) -> str:
    """Generate decode functions for each builtin type."""
    decoders: list[str] = []

    for type_name, atomic_type in sorted(builtin_types.items()):
        cpp_type: str | None = atomic_type.cpp_type
        desc: str = atomic_type.description

        if cpp_type is None:
            continue

        if type_name == "bool":
            decoders.append(f"""
/**
 * Decode bool (1 byte)
 * {desc}
 */
static inline bool decodeBool(
    const uint8_t*& buf, size_t& remaining, bool& out) {{

    if (remaining < 1) return false;

    out = (*buf++) != 0x00;
    remaining -= 1;
    return true;
}}
""")

        elif type_name == "uint8":
            decoders.append(f"""
/**
 * Decode uint8 (1 byte, direct)
 * {desc}
 */
static inline bool decodeUint8(
    const uint8_t*& buf, size_t& remaining, uint8_t& out) {{

    if (remaining < 1) return false;

    out = *buf++;
    remaining -= 1;
    return true;
}}
""")

        elif type_name == "int8":
            decoders.append(f"""
/**
 * Decode int8 (1 byte, direct)
 * {desc}
 */
static inline bool decodeInt8(
    const uint8_t*& buf, size_t& remaining, int8_t& out) {{

    if (remaining < 1) return false;

    out = static_cast<int8_t>(*buf++);
    remaining -= 1;
    return true;
}}
""")

        elif type_name == "uint16":
            decoders.append(f"""
/**
 * Decode uint16 (2 bytes, little-endian)
 * {desc}
 */
static inline bool decodeUint16(
    const uint8_t*& buf, size_t& remaining, uint16_t& out) {{

    if (remaining < 2) return false;

    out = buf[0] | (static_cast<uint16_t>(buf[1]) << 8);
    buf += 2;
    remaining -= 2;
    return true;
}}
""")

        elif type_name == "int16":
            decoders.append(f"""
/**
 * Decode int16 (2 bytes, little-endian)
 * {desc}
 */
static inline bool decodeInt16(
    const uint8_t*& buf, size_t& remaining, int16_t& out) {{

    if (remaining < 2) return false;

    uint16_t bits = buf[0] | (static_cast<uint16_t>(buf[1]) << 8);
    out = static_cast<int16_t>(bits);
    buf += 2;
    remaining -= 2;
    return true;
}}
""")

        elif type_name == "uint32":
            decoders.append(f"""
/**
 * Decode uint32 (4 bytes, little-endian)
 * {desc}
 */
static inline bool decodeUint32(
    const uint8_t*& buf, size_t& remaining, uint32_t& out) {{

    if (remaining < 4) return false;

    out = buf[0]
        | (static_cast<uint32_t>(buf[1]) << 8)
        | (static_cast<uint32_t>(buf[2]) << 16)
        | (static_cast<uint32_t>(buf[3]) << 24);
    buf += 4;
    remaining -= 4;
    return true;
}}
""")

        elif type_name == "int32":
            decoders.append(f"""
/**
 * Decode int32 (4 bytes, little-endian)
 * {desc}
 */
static inline bool decodeInt32(
    const uint8_t*& buf, size_t& remaining, int32_t& out) {{

    if (remaining < 4) return false;

    uint32_t bits = buf[0]
                  | (static_cast<uint32_t>(buf[1]) << 8)
                  | (static_cast<uint32_t>(buf[2]) << 16)
                  | (static_cast<uint32_t>(buf[3]) << 24);
    out = static_cast<int32_t>(bits);
    buf += 4;
    remaining -= 4;
    return true;
}}
""")

        elif type_name == "float32":
            decoders.append(f"""
/**
 * Decode float32 (4 bytes, IEEE 754 little-endian)
 * {desc}
 */
static inline bool decodeFloat32(
    const uint8_t*& buf, size_t& remaining, float& out) {{

    if (remaining < 4) return false;

    uint32_t bits = buf[0]
                  | (static_cast<uint32_t>(buf[1]) << 8)
                  | (static_cast<uint32_t>(buf[2]) << 16)
                  | (static_cast<uint32_t>(buf[3]) << 24);
    buf += 4;
    remaining -= 4;

    memcpy(&out, &bits, sizeof(float));
    return true;
}}
""")

        elif type_name == "norm8":
            decoders.append(f"""
/**
 * Decode norm8 (1 byte -> float 0.0-1.0)
 * {desc}
 */
static inline bool decodeNorm8(
    const uint8_t*& buf, size_t& remaining, float& out) {{

    if (remaining < 1) return false;

    uint8_t val = *buf++;
    remaining -= 1;

    out = static_cast<float>(val) / 255.0f;
    return true;
}}
""")

        elif type_name == "norm16":
            decoders.append(f"""
/**
 * Decode norm16 (2 bytes -> float 0.0-1.0)
 * {desc}
 */
static inline bool decodeNorm16(
    const uint8_t*& buf, size_t& remaining, float& out) {{

    if (remaining < 2) return false;

    uint16_t val = buf[0] | (static_cast<uint16_t>(buf[1]) << 8);
    buf += 2;
    remaining -= 2;

    out = static_cast<float>(val) / 65535.0f;
    return true;
}}
""")

        elif type_name == "string":
            decoders.append(f"""
/**
 * Decode string (variable length)
 * {desc}
 */
static inline bool decodeString(
    const uint8_t*& buf, size_t& remaining, std::string& out) {{

    if (remaining < 1) return false;

    uint8_t len = *buf++;
    remaining -= 1;

    if (remaining < len) return false;

    out.assign(reinterpret_cast<const char*>(buf), len);
    buf += len;
    remaining -= len;
    return true;
}}
""")

    return "\n".join(decoders)


def _generate_footer() -> str:
    """Generate namespace closing and file footer."""
    return """
}  // namespace Protocol
"""
