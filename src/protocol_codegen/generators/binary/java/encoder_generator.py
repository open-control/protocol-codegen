"""
Java Encoder Generator for Binary Protocol
Generates Encoder.java with 8-bit binary streaming encoding methods.

This generator creates static streaming write methods for all builtin types.
Uses full 8-bit byte range for maximum efficiency with zero allocations.

Key Features:
- Direct 8-bit encoding (no 7-bit constraint)
- Little-endian byte order for multi-byte types
- Streaming pattern: writeXxx(buffer, offset, value) returns bytes written
- Zero allocation - writes directly to provided buffer
- Auto-generated from builtin_types.yaml

Generated Output:
- Encoder.java (~150 lines)
- Package: Configurable via plugin_paths
- All methods: public static (utility class)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import AtomicType, TypeRegistry


def generate_encoder_java(type_registry: TypeRegistry, output_path: Path, package: str) -> str:
    """
    Generate Encoder.java with 8-bit encode methods for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Encoder.java will be written
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
    encoders = _generate_encoders(builtin_types)
    footer = _generate_footer()

    return f"{header}\n{encoders}\n{footer}"


def _generate_header(builtin_types: dict[str, AtomicType], package: str) -> str:
    """Generate file header with package and class declaration."""
    type_list = ", ".join(builtin_types.keys())

    return f"""package {package};

/**
 * Encoder - 8-bit Binary Streaming Encoder (Binary Protocol)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: builtin_types.yaml
 *
 * This class provides static streaming write methods for all builtin primitive
 * types. Uses full 8-bit byte range for efficient zero-allocation encoding.
 *
 * Supported types: {type_list}
 *
 * Encoding Strategy:
 * - Streaming pattern: writeXxx(buffer, offset, value) returns bytes written
 * - Direct byte writes to provided buffer (zero allocation)
 * - Little-endian for multi-byte integers
 * - IEEE 754 for floats
 * - 8-bit length prefix for strings/arrays
 *
 * Performance:
 * - Zero allocation per encode call
 * - Direct buffer manipulation
 * - Compiler-optimized inline writes
 */
public final class Encoder {{

    // Private constructor prevents instantiation (utility class)
    private Encoder() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // STREAMING WRITE METHODS (Type -> buffer, returns bytes written)
    // ============================================================================
"""


def _generate_encoders(builtin_types: dict[str, AtomicType]) -> str:
    """Generate streaming write methods for each builtin type."""
    encoders: list[str] = []

    for type_name, atomic_type in sorted(builtin_types.items()):
        java_type = atomic_type.java_type
        desc = atomic_type.description

        if type_name == "bool":
            encoders.append(f"""
    /**
     * Write bool (1 byte: 0x00 or 0x01)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (1)
     */
    public static int writeBool(byte[] buffer, int offset, {java_type} value) {{
        buffer[offset] = (byte) (value ? 0x01 : 0x00);
        return 1;
    }}
""")

        elif type_name == "uint8":
            encoders.append(f"""
    /**
     * Write uint8 (1 byte, direct)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode (treated as unsigned)
     * @return Number of bytes written (1)
     */
    public static int writeUint8(byte[] buffer, int offset, {java_type} value) {{
        buffer[offset] = (byte) (value & 0xFF);
        return 1;
    }}
""")

        elif type_name == "int8":
            encoders.append(f"""
    /**
     * Write int8 (1 byte, direct)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (1)
     */
    public static int writeInt8(byte[] buffer, int offset, {java_type} value) {{
        buffer[offset] = value;
        return 1;
    }}
""")

        elif type_name == "uint16":
            encoders.append(f"""
    /**
     * Write uint16 (2 bytes, little-endian)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode (treated as unsigned)
     * @return Number of bytes written (2)
     */
    public static int writeUint16(byte[] buffer, int offset, {java_type} value) {{
        int val = value & 0xFFFF;
        buffer[offset] = (byte) (val & 0xFF);
        buffer[offset + 1] = (byte) ((val >> 8) & 0xFF);
        return 2;
    }}
""")

        elif type_name == "int16":
            encoders.append(f"""
    /**
     * Write int16 (2 bytes, little-endian)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (2)
     */
    public static int writeInt16(byte[] buffer, int offset, {java_type} value) {{
        int bits = value & 0xFFFF;
        buffer[offset] = (byte) (bits & 0xFF);
        buffer[offset + 1] = (byte) ((bits >> 8) & 0xFF);
        return 2;
    }}
""")

        elif type_name == "uint32":
            encoders.append(f"""
    /**
     * Write uint32 (4 bytes, little-endian)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode (treated as unsigned)
     * @return Number of bytes written (4)
     */
    public static int writeUint32(byte[] buffer, int offset, {java_type} value) {{
        long val = value & 0xFFFFFFFFL;
        buffer[offset] = (byte) (val & 0xFF);
        buffer[offset + 1] = (byte) ((val >> 8) & 0xFF);
        buffer[offset + 2] = (byte) ((val >> 16) & 0xFF);
        buffer[offset + 3] = (byte) ((val >> 24) & 0xFF);
        return 4;
    }}
""")

        elif type_name == "int32":
            encoders.append(f"""
    /**
     * Write int32 (4 bytes, little-endian)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (4)
     */
    public static int writeInt32(byte[] buffer, int offset, {java_type} value) {{
        buffer[offset] = (byte) (value & 0xFF);
        buffer[offset + 1] = (byte) ((value >> 8) & 0xFF);
        buffer[offset + 2] = (byte) ((value >> 16) & 0xFF);
        buffer[offset + 3] = (byte) ((value >> 24) & 0xFF);
        return 4;
    }}
""")

        elif type_name == "float32":
            encoders.append(f"""
    /**
     * Write float32 (4 bytes, IEEE 754 little-endian)
     * {desc}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (4)
     */
    public static int writeFloat32(byte[] buffer, int offset, {java_type} value) {{
        int bits = Float.floatToRawIntBits(value);
        buffer[offset] = (byte) (bits & 0xFF);
        buffer[offset + 1] = (byte) ((bits >> 8) & 0xFF);
        buffer[offset + 2] = (byte) ((bits >> 16) & 0xFF);
        buffer[offset + 3] = (byte) ((bits >> 24) & 0xFF);
        return 4;
    }}
""")

        elif type_name == "norm8":
            encoders.append(f"""
    /**
     * Write norm8 (1 byte, full 8-bit range)
     * {desc}
     *
     * Converts float 0.0-1.0 to 8-bit value 0-255 for optimal precision.
     * Precision: ~0.4% (1/255), better than 7-bit norm8.
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Number of bytes written (1)
     */
    public static int writeNorm8(byte[] buffer, int offset, {java_type} value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        buffer[offset] = (byte) (Math.round(clamped * 255.0f) & 0xFF);
        return 1;
    }}
""")

        elif type_name == "norm16":
            encoders.append(f"""
    /**
     * Write norm16 (2 bytes, little-endian)
     * {desc}
     *
     * Converts float 0.0-1.0 to uint16 0-65535 for high precision.
     * Precision: ~0.0015% (1/65535)
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Number of bytes written (2)
     */
    public static int writeNorm16(byte[] buffer, int offset, {java_type} value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        int val = Math.round(clamped * 65535.0f) & 0xFFFF;
        buffer[offset] = (byte) (val & 0xFF);
        buffer[offset + 1] = (byte) ((val >> 8) & 0xFF);
        return 2;
    }}
""")

        elif type_name == "string":
            encoders.append(f"""
    /**
     * Write string (variable length: 1 byte length + data)
     * {desc}
     *
     * Format: [length (8-bit)] [char0] [char1] ... [charN-1]
     * Max length: 255 chars (8-bit length encoding)
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value String to encode
     * @param maxLength Maximum allowed string length
     * @return Number of bytes written (1 + string.length)
     */
    public static int writeString(byte[] buffer, int offset, String value, int maxLength) {{
        if (value == null) {{
            value = "";
        }}

        int len = Math.min(value.length(), Math.min(maxLength, 255));
        buffer[offset] = (byte) len;

        for (int i = 0; i < len; i++) {{
            buffer[offset + 1 + i] = (byte) value.charAt(i);
        }}

        return 1 + len;
    }}
""")

    return "\n".join(encoders)


def _generate_footer() -> str:
    """Generate class closing."""
    return """
}  // class Encoder
"""
