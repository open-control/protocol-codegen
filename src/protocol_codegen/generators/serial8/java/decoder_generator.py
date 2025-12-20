"""
Java Decoder Generator for Serial8 Protocol
Generates Decoder.java with 8-bit binary decoding methods.

This generator creates static decode methods for all builtin types.
Decodes 8-bit binary bytes to native types.

Key Features:
- Direct 8-bit decoding (no 7-bit constraint)
- Little-endian byte order for multi-byte types
- Static methods with byte[] arrays
- Java exceptions for error handling

Generated Output:
- Decoder.java (~120 lines)
- Package: Configurable via plugin_paths
- All methods: public static (utility class)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import AtomicType, TypeRegistry


def generate_decoder_java(type_registry: TypeRegistry, output_path: Path, package: str) -> str:
    """
    Generate Decoder.java with 8-bit decode methods for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Decoder.java will be written
        package: Java package name (e.g., 'protocol' or 'com.example.protocol')

    Returns:
        Generated Java code as string
    """
    builtin_types: dict[str, AtomicType] = {
        name: atomic_type
        for name, atomic_type in type_registry.types.items()
        if atomic_type.is_builtin
    }

    header = _generate_header(builtin_types, package)
    decoders = _generate_decoders(builtin_types)
    footer = _generate_footer()

    return f"{header}\n{decoders}\n{footer}"


def _generate_header(builtin_types: dict[str, AtomicType], package: str) -> str:
    """Generate file header with package and class declaration."""
    type_list = ", ".join(builtin_types.keys())

    return f"""package {package};

/**
 * Decoder - 8-bit Binary Decoder (Serial8 Protocol)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: builtin_types.yaml
 *
 * This class provides static decode methods for all builtin primitive
 * types. Decodes 8-bit binary bytes to native types.
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
 * - Static methods for zero overhead
 * - Direct byte array manipulation
 * - More efficient than 7-bit decoding
 *
 * Companion file: Encoder.java
 */
public final class Decoder {{

    // Private constructor prevents instantiation (utility class)
    private Decoder() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // DECODE METHODS (8-bit binary bytes -> Type)
    // ============================================================================
    // Returns decoded value or throws IllegalArgumentException on error
"""


def _generate_decoders(builtin_types: dict[str, AtomicType]) -> str:
    """Generate decode methods for each builtin type."""
    decoders: list[str] = []

    for type_name, atomic_type in sorted(builtin_types.items()):
        java_type = atomic_type.java_type
        desc = atomic_type.description

        if type_name == "bool":
            decoders.append(f"""
    /**
     * Decode bool (1 byte)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeBool(byte[] data, int offset) {{
        if (data.length - offset < 1) {{
            throw new IllegalArgumentException("Insufficient data for bool decode");
        }}
        return data[offset] != 0x00;
    }}
""")

        elif type_name == "uint8":
            decoders.append(f"""
    /**
     * Decode uint8 (1 byte, direct)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value (unsigned, returned as {java_type})
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeUint8(byte[] data, int offset) {{
        if (data.length - offset < 1) {{
            throw new IllegalArgumentException("Insufficient data for uint8 decode");
        }}
        return (data[offset] & 0xFF);
    }}
""")

        elif type_name == "int8":
            decoders.append(f"""
    /**
     * Decode int8 (1 byte, direct)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeInt8(byte[] data, int offset) {{
        if (data.length - offset < 1) {{
            throw new IllegalArgumentException("Insufficient data for int8 decode");
        }}
        return data[offset];
    }}
""")

        elif type_name == "uint16":
            decoders.append(f"""
    /**
     * Decode uint16 (2 bytes, little-endian)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value (unsigned, returned as {java_type})
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeUint16(byte[] data, int offset) {{
        if (data.length - offset < 2) {{
            throw new IllegalArgumentException("Insufficient data for uint16 decode");
        }}

        return (data[offset] & 0xFF)
                | ((data[offset + 1] & 0xFF) << 8);
    }}
""")

        elif type_name == "int16":
            decoders.append(f"""
    /**
     * Decode int16 (2 bytes, little-endian)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeInt16(byte[] data, int offset) {{
        if (data.length - offset < 2) {{
            throw new IllegalArgumentException("Insufficient data for int16 decode");
        }}

        int bits = (data[offset] & 0xFF)
                 | ((data[offset + 1] & 0xFF) << 8);

        return (short) bits;
    }}
""")

        elif type_name == "uint32":
            decoders.append(f"""
    /**
     * Decode uint32 (4 bytes, little-endian)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value (unsigned, returned as {java_type})
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeUint32(byte[] data, int offset) {{
        if (data.length - offset < 4) {{
            throw new IllegalArgumentException("Insufficient data for uint32 decode");
        }}

        long val = (data[offset] & 0xFFL)
                 | ((data[offset + 1] & 0xFFL) << 8)
                 | ((data[offset + 2] & 0xFFL) << 16)
                 | ((data[offset + 3] & 0xFFL) << 24);

        return (int) val;
    }}
""")

        elif type_name == "int32":
            decoders.append(f"""
    /**
     * Decode int32 (4 bytes, little-endian)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeInt32(byte[] data, int offset) {{
        if (data.length - offset < 4) {{
            throw new IllegalArgumentException("Insufficient data for int32 decode");
        }}

        return (data[offset] & 0xFF)
             | ((data[offset + 1] & 0xFF) << 8)
             | ((data[offset + 2] & 0xFF) << 16)
             | ((data[offset + 3] & 0xFF) << 24);
    }}
""")

        elif type_name == "float32":
            decoders.append(f"""
    /**
     * Decode float32 (4 bytes, IEEE 754 little-endian)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded value
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeFloat32(byte[] data, int offset) {{
        if (data.length - offset < 4) {{
            throw new IllegalArgumentException("Insufficient data for float32 decode");
        }}

        int bits = (data[offset] & 0xFF)
                 | ((data[offset + 1] & 0xFF) << 8)
                 | ((data[offset + 2] & 0xFF) << 16)
                 | ((data[offset + 3] & 0xFF) << 24);

        return Float.intBitsToFloat(bits);
    }}
""")

        elif type_name == "norm8":
            decoders.append(f"""
    /**
     * Decode norm8 (1 byte -> float 0.0-1.0)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded normalized float value (0.0-1.0)
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeNorm8(byte[] data, int offset) {{
        if (data.length - offset < 1) {{
            throw new IllegalArgumentException("Insufficient data for norm8 decode");
        }}

        int val = data[offset] & 0xFF;
        return val / 255.0f;
    }}
""")

        elif type_name == "norm16":
            decoders.append(f"""
    /**
     * Decode norm16 (2 bytes -> float 0.0-1.0)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @return Decoded normalized float value (0.0-1.0)
     * @throws IllegalArgumentException if insufficient data
     */
    public static {java_type} decodeNorm16(byte[] data, int offset) {{
        if (data.length - offset < 2) {{
            throw new IllegalArgumentException("Insufficient data for norm16 decode");
        }}

        int val = (data[offset] & 0xFF)
                | ((data[offset + 1] & 0xFF) << 8);

        return val / 65535.0f;
    }}
""")

        elif type_name == "string":
            decoders.append(f"""
    /**
     * Decode string (variable length)
     * {desc}
     *
     * @param data Byte array containing encoded data
     * @param offset Start offset in array
     * @param maxLength Maximum allowed string length
     * @return Decoded string
     * @throws IllegalArgumentException if insufficient data or string too long
     */
    public static String decodeString(byte[] data, int offset, int maxLength) {{
        if (data.length - offset < 1) {{
            throw new IllegalArgumentException("Insufficient data for string decode");
        }}

        int len = data[offset] & 0xFF;
        offset++;

        if (data.length - offset < len) {{
            throw new IllegalArgumentException("Insufficient data for string content");
        }}

        if (len > maxLength) {{
            throw new IllegalArgumentException(
                "String length " + len + " exceeds maximum " + maxLength);
        }}

        return new String(data, offset, len);
    }}
""")

    return "\n".join(decoders)


def _generate_footer() -> str:
    """Generate class closing."""
    return """
}  // class Decoder
"""
