"""
C++ Encoder Generator for Serial8 Protocol
Generates Encoder.hpp with 8-bit binary encoding functions.

This generator creates static encode functions for all builtin
types. Uses full 8-bit byte range for maximum efficiency.

Key Features:
- Direct 8-bit encoding (no 7-bit constraint)
- Little-endian byte order for multi-byte types
- Static functions in struct (zero runtime overhead, header-only)

Generated Output:
- Encoder.hpp (~100 lines)
- Namespace: Protocol
- All functions: static (header-only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import AtomicType, TypeRegistry


def generate_encoder_hpp(type_registry: TypeRegistry, output_path: Path) -> str:
    """
    Generate Encoder.hpp with 8-bit encode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Encoder.hpp will be written

    Returns:
        Generated C++ code as string
    """
    builtin_types: dict[str, AtomicType] = {
        name: atomic_type
        for name, atomic_type in type_registry.types.items()
        if atomic_type.is_builtin
    }

    header = _generate_header(builtin_types)
    encoders = _generate_encoders(builtin_types)
    footer = _generate_footer()

    return f"{header}\n{encoders}\n{footer}"


def _generate_header(builtin_types: dict[str, AtomicType]) -> str:
    """Generate file header with includes and namespace."""
    type_list = ", ".join(builtin_types.keys())

    return f"""/**
 * Encoder.hpp - 8-bit Binary Encoder (Serial8 Protocol)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: builtin_types.yaml
 *
 * This file provides static inline encode functions for all builtin
 * primitive types. Uses full 8-bit byte range for efficient encoding.
 *
 * Supported types: {type_list}
 *
 * Encoding Strategy:
 * - Direct byte writes (no 7-bit constraint)
 * - Little-endian for multi-byte integers
 * - IEEE 754 for floats (native byte order)
 * - 8-bit length prefix for strings/arrays
 *
 * Performance:
 * - Static functions in struct = zero runtime overhead
 * - Compiler optimizes away function calls
 * - More efficient than 7-bit encoding (no expansion)
 *
 * Companion file: Decoder.hpp
 */

#pragma once

#include <cmath>
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>

namespace Protocol {{

// ============================================================================
// ENCODE FUNCTIONS (Type -> 8-bit binary bytes)
// ============================================================================
"""


def _generate_encoders(builtin_types: dict[str, AtomicType]) -> str:
    """Generate encode functions for each builtin type."""
    encoders: list[str] = []

    for type_name, atomic_type in sorted(builtin_types.items()):
        cpp_type: str | None = atomic_type.cpp_type
        desc: str = atomic_type.description

        if cpp_type is None:
            continue

        if type_name == "bool":
            encoders.append(f"""
/**
 * Encode bool (1 byte: 0x00 or 0x01)
 * {desc}
 */
static void encodeBool(uint8_t*& buf, bool val) {{
    *buf++ = val ? 0x01 : 0x00;
}}
""")

        elif type_name == "uint8":
            encoders.append(f"""
/**
 * Encode uint8 (1 byte, direct)
 * {desc}
 */
static void encodeUint8(uint8_t*& buf, uint8_t val) {{
    *buf++ = val;
}}
""")

        elif type_name == "int8":
            encoders.append(f"""
/**
 * Encode int8 (1 byte, direct)
 * {desc}
 */
static void encodeInt8(uint8_t*& buf, int8_t val) {{
    *buf++ = static_cast<uint8_t>(val);
}}
""")

        elif type_name == "uint16":
            encoders.append(f"""
/**
 * Encode uint16 (2 bytes, little-endian)
 * {desc}
 */
static void encodeUint16(uint8_t*& buf, uint16_t val) {{
    *buf++ = val & 0xFF;         // low byte
    *buf++ = (val >> 8) & 0xFF;  // high byte
}}
""")

        elif type_name == "int16":
            encoders.append(f"""
/**
 * Encode int16 (2 bytes, little-endian)
 * {desc}
 */
static void encodeInt16(uint8_t*& buf, int16_t val) {{
    uint16_t bits = static_cast<uint16_t>(val);
    *buf++ = bits & 0xFF;
    *buf++ = (bits >> 8) & 0xFF;
}}
""")

        elif type_name == "uint32":
            encoders.append(f"""
/**
 * Encode uint32 (4 bytes, little-endian)
 * {desc}
 */
static void encodeUint32(uint8_t*& buf, uint32_t val) {{
    *buf++ = val & 0xFF;
    *buf++ = (val >> 8) & 0xFF;
    *buf++ = (val >> 16) & 0xFF;
    *buf++ = (val >> 24) & 0xFF;
}}
""")

        elif type_name == "int32":
            encoders.append(f"""
/**
 * Encode int32 (4 bytes, little-endian)
 * {desc}
 */
static void encodeInt32(uint8_t*& buf, int32_t val) {{
    uint32_t bits = static_cast<uint32_t>(val);
    *buf++ = bits & 0xFF;
    *buf++ = (bits >> 8) & 0xFF;
    *buf++ = (bits >> 16) & 0xFF;
    *buf++ = (bits >> 24) & 0xFF;
}}
""")

        elif type_name == "float32":
            encoders.append(f"""
/**
 * Encode float32 (4 bytes, IEEE 754 little-endian)
 * {desc}
 */
static void encodeFloat32(uint8_t*& buf, float val) {{
    uint32_t bits;
    memcpy(&bits, &val, sizeof(float));

    *buf++ = bits & 0xFF;
    *buf++ = (bits >> 8) & 0xFF;
    *buf++ = (bits >> 16) & 0xFF;
    *buf++ = (bits >> 24) & 0xFF;
}}
""")

        elif type_name == "norm8":
            encoders.append(f"""
/**
 * Encode norm8 (1 byte, full 8-bit range)
 * {desc}
 *
 * Converts float 0.0-1.0 to 8-bit value 0-255 for optimal precision.
 * Precision: ~0.4% (1/255), better than 7-bit norm8.
 */
static void encodeNorm8(uint8_t*& buf, float val) {{
    if (val < 0.0f) val = 0.0f;
    if (val > 1.0f) val = 1.0f;
    *buf++ = static_cast<uint8_t>(std::lroundf(val * 255.0f));
}}
""")

        elif type_name == "norm16":
            encoders.append(f"""
/**
 * Encode norm16 (2 bytes, little-endian)
 * {desc}
 *
 * Converts float 0.0-1.0 to uint16 0-65535 for high precision.
 * Precision: ~0.0015% (1/65535)
 */
static void encodeNorm16(uint8_t*& buf, float val) {{
    if (val < 0.0f) val = 0.0f;
    if (val > 1.0f) val = 1.0f;
    uint16_t norm = static_cast<uint16_t>(std::lroundf(val * 65535.0f));

    *buf++ = norm & 0xFF;
    *buf++ = (norm >> 8) & 0xFF;
}}
""")

        elif type_name == "string":
            encoders.append(f"""
/**
 * Encode string (variable length: 1 byte length + data)
 * {desc}
 *
 * Format: [length (8-bit)] [char0] [char1] ... [charN-1]
 * Max length: 255 chars (8-bit length encoding)
 */
static void encodeString(uint8_t*& buf, const std::string& str) {{
    uint8_t len = static_cast<uint8_t>(str.length());  // Max 255
    *buf++ = len;

    for (size_t i = 0; i < len; ++i) {{
        *buf++ = static_cast<uint8_t>(str[i]);
    }}
}}
""")

    return "\n".join(encoders)


def _generate_footer() -> str:
    """Generate namespace closing and file footer."""
    return """
}  // namespace Protocol
"""
