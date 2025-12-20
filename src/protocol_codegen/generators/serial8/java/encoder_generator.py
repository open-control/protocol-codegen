"""
Java Encoder Generator for Serial8 Protocol
Generates Encoder.java with 8-bit binary encoding methods.

This generator creates static encode methods for all builtin types.
Uses full 8-bit byte range for maximum efficiency.

Key Features:
- Direct 8-bit encoding (no 7-bit constraint)
- Little-endian byte order for multi-byte types
- Static methods with byte[] arrays
- Auto-generated from builtin_types.yaml

Generated Output:
- Encoder.java (~120 lines)
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
 * Encoder - 8-bit Binary Encoder (Serial8 Protocol)
 *
 * AUTO-GENERATED - DO NOT EDIT
 * Generated from: builtin_types.yaml
 *
 * This class provides static encode methods for all builtin primitive
 * types. Uses full 8-bit byte range for efficient encoding.
 *
 * Supported types: {type_list}
 *
 * Encoding Strategy:
 * - Direct byte writes (no 7-bit constraint)
 * - Little-endian for multi-byte integers
 * - IEEE 754 for floats
 * - 8-bit length prefix for strings/arrays
 *
 * Performance:
 * - Static methods for zero overhead
 * - Direct byte array manipulation
 * - More efficient than 7-bit encoding (no expansion)
 */
public final class Encoder {{

    // Private constructor prevents instantiation (utility class)
    private Encoder() {{
        throw new AssertionError("Utility class cannot be instantiated");
    }}

    // ============================================================================
    // ENCODE METHODS (Type -> 8-bit binary bytes)
    // ============================================================================
"""


def _generate_encoders(builtin_types: dict[str, AtomicType]) -> str:
    """Generate encode methods for each builtin type."""
    encoders: list[str] = []

    for type_name, atomic_type in sorted(builtin_types.items()):
        java_type = atomic_type.java_type
        desc = atomic_type.description

        if type_name == "bool":
            encoders.append(f"""
    /**
     * Encode bool (1 byte: 0x00 or 0x01)
     * {desc}
     *
     * @param value Value to encode
     * @return Encoded byte array (1 byte)
     */
    public static byte[] encodeBool({java_type} value) {{
        return new byte[]{{ (byte) (value ? 0x01 : 0x00) }};
    }}
""")

        elif type_name == "uint8":
            encoders.append(f"""
    /**
     * Encode uint8 (1 byte, direct)
     * {desc}
     *
     * @param value Value to encode (treated as unsigned)
     * @return Encoded byte array (1 byte)
     */
    public static byte[] encodeUint8({java_type} value) {{
        return new byte[]{{ (byte) (value & 0xFF) }};
    }}
""")

        elif type_name == "int8":
            encoders.append(f"""
    /**
     * Encode int8 (1 byte, direct)
     * {desc}
     *
     * @param value Value to encode
     * @return Encoded byte array (1 byte)
     */
    public static byte[] encodeInt8({java_type} value) {{
        return new byte[]{{ (byte) value }};
    }}
""")

        elif type_name == "uint16":
            encoders.append(f"""
    /**
     * Encode uint16 (2 bytes, little-endian)
     * {desc}
     *
     * @param value Value to encode (treated as unsigned)
     * @return Encoded byte array (2 bytes)
     */
    public static byte[] encodeUint16({java_type} value) {{
        int val = value & 0xFFFF;
        return new byte[]{{
            (byte) (val & 0xFF),         // low byte
            (byte) ((val >> 8) & 0xFF)   // high byte
        }};
    }}
""")

        elif type_name == "int16":
            encoders.append(f"""
    /**
     * Encode int16 (2 bytes, little-endian)
     * {desc}
     *
     * @param value Value to encode
     * @return Encoded byte array (2 bytes)
     */
    public static byte[] encodeInt16({java_type} value) {{
        int bits = value & 0xFFFF;
        return new byte[]{{
            (byte) (bits & 0xFF),
            (byte) ((bits >> 8) & 0xFF)
        }};
    }}
""")

        elif type_name == "uint32":
            encoders.append(f"""
    /**
     * Encode uint32 (4 bytes, little-endian)
     * {desc}
     *
     * @param value Value to encode (treated as unsigned)
     * @return Encoded byte array (4 bytes)
     */
    public static byte[] encodeUint32({java_type} value) {{
        long val = value & 0xFFFFFFFFL;
        return new byte[]{{
            (byte) (val & 0xFF),
            (byte) ((val >> 8) & 0xFF),
            (byte) ((val >> 16) & 0xFF),
            (byte) ((val >> 24) & 0xFF)
        }};
    }}
""")

        elif type_name == "int32":
            encoders.append(f"""
    /**
     * Encode int32 (4 bytes, little-endian)
     * {desc}
     *
     * @param value Value to encode
     * @return Encoded byte array (4 bytes)
     */
    public static byte[] encodeInt32({java_type} value) {{
        return new byte[]{{
            (byte) (value & 0xFF),
            (byte) ((value >> 8) & 0xFF),
            (byte) ((value >> 16) & 0xFF),
            (byte) ((value >> 24) & 0xFF)
        }};
    }}
""")

        elif type_name == "float32":
            encoders.append(f"""
    /**
     * Encode float32 (4 bytes, IEEE 754 little-endian)
     * {desc}
     *
     * @param value Value to encode
     * @return Encoded byte array (4 bytes)
     */
    public static byte[] encodeFloat32({java_type} value) {{
        int bits = Float.floatToRawIntBits(value);
        return new byte[]{{
            (byte) (bits & 0xFF),
            (byte) ((bits >> 8) & 0xFF),
            (byte) ((bits >> 16) & 0xFF),
            (byte) ((bits >> 24) & 0xFF)
        }};
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
     *
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Encoded byte array (1 byte)
     */
    public static byte[] encodeNorm8({java_type} value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        int val = Math.round(clamped * 255.0f) & 0xFF;
        return new byte[]{{ (byte) val }};
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
     *
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Encoded byte array (2 bytes)
     */
    public static byte[] encodeNorm16({java_type} value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        int val = Math.round(clamped * 65535.0f) & 0xFFFF;
        return new byte[]{{
            (byte) (val & 0xFF),
            (byte) ((val >> 8) & 0xFF)
        }};
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
     *
     * @param value String to encode
     * @param maxLength Maximum allowed string length
     * @return Encoded byte array (1 + string.length bytes)
     */
    public static byte[] encodeString(String value, int maxLength) {{
        if (value == null) {{
            value = "";
        }}

        int len = Math.min(value.length(), Math.min(maxLength, 255));
        byte[] result = new byte[1 + len];

        result[0] = (byte) len;

        for (int i = 0; i < len; i++) {{
            result[1 + i] = (byte) value.charAt(i);
        }}

        return result;
    }}
""")

    return "\n".join(encoders)


def _generate_footer() -> str:
    """Generate class closing."""
    return """
}  // class Encoder
"""
