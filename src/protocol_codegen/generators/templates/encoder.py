"""
Encoder Template for generating Encoder.hpp/Encoder.java files.

Combines LanguageBackend (syntax) with EncodingStrategy (encoding logic)
to generate protocol-specific encoder code for any target language.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy
    from protocol_codegen.generators.common.encoding.strategy import (
        IntegerEncodingSpec,
        NormEncodingSpec,
        StringEncodingSpec,
    )


class EncoderTemplate:
    """Template for generating Encoder files.

    Generates complete encoder files for any combination of:
    - LanguageBackend: C++, Java, (future: Rust, Python, etc.)
    - EncodingStrategy: Serial8 (8-bit), SysEx (7-bit)
    """

    def __init__(
        self,
        backend: LanguageBackend,
        strategy: EncodingStrategy,
    ):
        """Initialize encoder template.

        Args:
            backend: Language backend for syntax
            strategy: Encoding strategy for protocol-specific logic
        """
        self.backend = backend
        self.strategy = strategy

    def generate(self, type_registry: TypeRegistry, output_path: Path) -> str:
        """Generate complete encoder file.

        Args:
            type_registry: Registry with builtin types
            output_path: Output file path (for header comment)

        Returns:
            Complete encoder file content
        """
        parts = [
            self._generate_header(output_path),
            self._generate_class_open(),
            self._generate_encoders(type_registry),
            self._generate_class_close(),
            self._generate_footer(),
        ]
        return "\n".join(filter(None, parts))

    def _generate_header(self, output_path: Path) -> str:
        """Generate file header with includes/imports."""
        if self.backend.name == "cpp":
            return self._generate_cpp_header(output_path)
        elif self.backend.name == "java":
            return self._generate_java_header(output_path)
        return ""

    def _generate_cpp_header(self, output_path: Path) -> str:
        """Generate C++ header."""
        return f"""#pragma once

{self.backend.auto_generated_comment(output_path.name)}

// {self.strategy.name} Encoder - {self.strategy.description}

#include <cstdint>
#include <cstring>
#include <string>

namespace Protocol {{
"""

    def _generate_java_header(self, output_path: Path) -> str:
        """Generate Java header."""
        package = getattr(self.backend, "package", "protocol")
        return f"""package {package};

{self.backend.auto_generated_comment(output_path.name)}

// {self.strategy.name} Encoder - {self.strategy.description}

"""

    def _generate_class_open(self) -> str:
        """Generate class/struct opening."""
        if self.backend.name == "cpp":
            return "struct Encoder {"
        elif self.backend.name == "java":
            return "public final class Encoder {"
        return ""

    def _generate_class_close(self) -> str:
        """Generate class/struct closing."""
        if self.backend.name == "cpp":
            return "};"
        elif self.backend.name == "java":
            return "}"
        return ""

    def _generate_footer(self) -> str:
        """Generate file footer."""
        if self.backend.name == "cpp":
            return "\n}  // namespace Protocol\n"
        return ""

    def _generate_encoders(self, type_registry: TypeRegistry) -> str:
        """Generate all encoder methods."""
        encoders: list[str] = []

        for type_name, atomic_type in sorted(type_registry.types.items()):
            if not atomic_type.is_builtin:
                continue

            encoder = self._generate_single_encoder(type_name, atomic_type.description)
            if encoder:
                encoders.append(encoder)

        return "\n".join(encoders)

    def _generate_single_encoder(self, type_name: str, description: str) -> str:
        """Generate encoder for a single type."""
        if type_name == "bool":
            return self._generate_bool_encoder(description)
        elif type_name in ("uint8", "int8", "uint16", "int16", "uint32", "int32"):
            return self._generate_integer_encoder(type_name, description)
        elif type_name == "float32":
            return self._generate_float_encoder(description)
        elif type_name in ("norm8", "norm16"):
            return self._generate_norm_encoder(type_name, description)
        elif type_name == "string":
            return self._generate_string_encoder(description)
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Bool Encoder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_bool_encoder(self, description: str) -> str:
        """Generate bool encoder."""
        true_val = self.strategy.bool_true_value
        false_val = self.strategy.bool_false_value

        if self.backend.name == "cpp":
            return f"""
/**
 * Encode bool (1 byte: 0x{false_val:02X} or 0x{true_val:02X})
 * {description}
 */
static inline void encodeBool(uint8_t*& buf, bool val) {{
    *buf++ = val ? 0x{true_val:02X} : 0x{false_val:02X};
}}
"""
        elif self.backend.name == "java":
            return f"""
    /**
     * Write bool (1 byte: 0x{false_val:02X} or 0x{true_val:02X})
     * {description}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written (1)
     */
    public static int writeBool(byte[] buffer, int offset, boolean value) {{
        buffer[offset] = (byte) (value ? 0x{true_val:02X} : 0x{false_val:02X});
        return 1;
    }}
"""
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Integer Encoder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_integer_encoder(self, type_name: str, description: str) -> str:
        """Generate integer encoder using spec."""
        spec = self.strategy.get_integer_spec(type_name)
        if not spec:
            return ""

        if self.backend.name == "cpp":
            return self._generate_cpp_integer_encoder(type_name, spec, description)
        elif self.backend.name == "java":
            return self._generate_java_integer_encoder(type_name, spec, description)
        return ""

    def _generate_cpp_integer_encoder(
        self, type_name: str, spec: IntegerEncodingSpec, description: str
    ) -> str:
        """Generate C++ integer encoder."""
        # Get C++ type
        cpp_type = {
            "uint8": "uint8_t",
            "int8": "int8_t",
            "uint16": "uint16_t",
            "int16": "int16_t",
            "uint32": "uint32_t",
            "int32": "int32_t",
        }.get(type_name, "uint8_t")

        method_name = f"encode{type_name.capitalize()}"

        # Generate byte writes
        lines: list[str] = []
        for shift, mask in zip(spec.shifts, spec.masks, strict=True):
            expr = f"val & 0x{mask:02X}" if shift == 0 else f"(val >> {shift}) & 0x{mask:02X}"
            lines.append(f"    *buf++ = {expr};")

        body = "\n".join(lines)

        # For signed types, cast to unsigned first
        cast_line = ""
        if type_name.startswith("int") and spec.byte_count > 1:
            cpp_unsigned = cpp_type.replace("int", "uint")
            cast_line = f"    {cpp_unsigned} val = static_cast<{cpp_unsigned}>(value);\n"
            body = body.replace("val", "val")
            return f"""
/**
 * Encode {type_name} ({spec.comment})
 * {description}
 */
static inline void {method_name}(uint8_t*& buf, {cpp_type} value) {{
{cast_line}{body}
}}
"""
        else:
            return f"""
/**
 * Encode {type_name} ({spec.comment})
 * {description}
 */
static inline void {method_name}(uint8_t*& buf, {cpp_type} val) {{
{body}
}}
"""

    def _generate_java_integer_encoder(
        self, type_name: str, spec: IntegerEncodingSpec, description: str
    ) -> str:
        """Generate Java integer encoder."""
        # Get Java type
        java_type = {
            "uint8": "int",
            "int8": "byte",
            "uint16": "int",
            "int16": "short",
            "uint32": "long",
            "int32": "int",
        }.get(type_name, "int")

        method_name = f"write{type_name.capitalize()}"

        # Generate byte writes
        lines: list[str] = []
        for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True)):
            expr = (
                f"(byte) (val & 0x{mask:02X})"
                if shift == 0
                else f"(byte) ((val >> {shift}) & 0x{mask:02X})"
            )
            lines.append(f"        buffer[offset + {i}] = {expr};")

        body = "\n".join(lines)

        # For uint types in Java, mask to prevent sign issues
        cast_line = ""
        if type_name == "uint8":
            cast_line = "        int val = value & 0xFF;\n"
        elif type_name == "uint16":
            cast_line = "        int val = value & 0xFFFF;\n"
        elif type_name == "uint32":
            cast_line = "        long val = value & 0xFFFFFFFFL;\n"
        elif type_name in ("int16", "int32"):
            if spec.byte_count > 1:
                cast_line = f"        int val = value & 0x{'FF' * (spec.byte_count if spec.byte_count <= 4 else 4)};\n"
            else:
                cast_line = ""
        else:
            cast_line = ""

        # For simple int8, just use value directly
        if type_name == "int8" and spec.byte_count == 1:
            return f"""
    /**
     * Write {type_name} ({spec.comment})
     * {description}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written ({spec.byte_count})
     */
    public static int {method_name}(byte[] buffer, int offset, {java_type} value) {{
        buffer[offset] = value;
        return {spec.byte_count};
    }}
"""

        return f"""
    /**
     * Write {type_name} ({spec.comment})
     * {description}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written ({spec.byte_count})
     */
    public static int {method_name}(byte[] buffer, int offset, {java_type} value) {{
{cast_line}{body}
        return {spec.byte_count};
    }}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Float32 Encoder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_float_encoder(self, description: str) -> str:
        """Generate float32 encoder."""
        spec = self.strategy.get_integer_spec("float32")
        if not spec:
            return ""

        if self.backend.name == "cpp":
            return self._generate_cpp_float_encoder(spec, description)
        elif self.backend.name == "java":
            return self._generate_java_float_encoder(spec, description)
        return ""

    def _generate_cpp_float_encoder(
        self, spec: IntegerEncodingSpec, description: str
    ) -> str:
        """Generate C++ float32 encoder."""
        lines: list[str] = []
        for shift, mask in zip(spec.shifts, spec.masks, strict=True):
            expr = f"bits & 0x{mask:02X}" if shift == 0 else f"(bits >> {shift}) & 0x{mask:02X}"
            lines.append(f"    *buf++ = {expr};")

        body = "\n".join(lines)

        return f"""
/**
 * Encode float32 ({spec.comment})
 * {description}
 */
static inline void encodeFloat32(uint8_t*& buf, float val) {{
    uint32_t bits;
    memcpy(&bits, &val, sizeof(float));

{body}
}}
"""

    def _generate_java_float_encoder(
        self, spec: IntegerEncodingSpec, description: str
    ) -> str:
        """Generate Java float32 encoder."""
        lines: list[str] = []
        for i, (shift, mask) in enumerate(zip(spec.shifts, spec.masks, strict=True)):
            expr = (
                f"(byte) (bits & 0x{mask:02X})"
                if shift == 0
                else f"(byte) ((bits >> {shift}) & 0x{mask:02X})"
            )
            lines.append(f"        buffer[offset + {i}] = {expr};")

        body = "\n".join(lines)

        return f"""
    /**
     * Write float32 ({spec.comment})
     * {description}
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Value to encode
     * @return Number of bytes written ({spec.byte_count})
     */
    public static int writeFloat32(byte[] buffer, int offset, float value) {{
        int bits = Float.floatToRawIntBits(value);
{body}
        return {spec.byte_count};
    }}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Norm Encoder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_norm_encoder(self, type_name: str, description: str) -> str:
        """Generate norm8/norm16 encoder."""
        spec = self.strategy.get_norm_spec(type_name)
        if not spec:
            return ""

        if self.backend.name == "cpp":
            return self._generate_cpp_norm_encoder(type_name, spec, description)
        elif self.backend.name == "java":
            return self._generate_java_norm_encoder(type_name, spec, description)
        return ""

    def _generate_cpp_norm_encoder(
        self, type_name: str, spec: NormEncodingSpec, description: str
    ) -> str:
        """Generate C++ norm encoder."""
        method_name = f"encode{type_name.capitalize()}"
        max_val = spec.max_value

        if spec.byte_count == 1:
            # Single byte norm
            byte_mask = 0x7F if max_val == 127 else 0xFF
            return f"""
/**
 * Encode {type_name} ({spec.comment})
 * {description}
 *
 * Converts float 0.0-1.0 to value 0-{max_val}.
 */
static inline void {method_name}(uint8_t*& buf, float val) {{
    if (val < 0.0f) val = 0.0f;
    if (val > 1.0f) val = 1.0f;
    *buf++ = static_cast<uint8_t>(val * {max_val}.0f + 0.5f) & 0x{byte_mask:02X};
}}
"""
        else:
            # Multi-byte norm (use integer spec)
            int_spec = spec.integer_spec
            if not int_spec:
                return ""

            lines: list[str] = []
            for shift, mask in zip(int_spec.shifts, int_spec.masks, strict=True):
                expr = f"norm & 0x{mask:02X}" if shift == 0 else f"(norm >> {shift}) & 0x{mask:02X}"
                lines.append(f"    *buf++ = {expr};")

            body = "\n".join(lines)

            return f"""
/**
 * Encode {type_name} ({spec.comment})
 * {description}
 *
 * Converts float 0.0-1.0 to uint16 0-{max_val}.
 */
static inline void {method_name}(uint8_t*& buf, float val) {{
    if (val < 0.0f) val = 0.0f;
    if (val > 1.0f) val = 1.0f;
    uint16_t norm = static_cast<uint16_t>(val * {max_val}.0f + 0.5f);

{body}
}}
"""

    def _generate_java_norm_encoder(
        self, type_name: str, spec: NormEncodingSpec, description: str
    ) -> str:
        """Generate Java norm encoder."""
        method_name = f"write{type_name.capitalize()}"
        max_val = spec.max_value

        if spec.byte_count == 1:
            byte_mask = 0x7F if max_val == 127 else 0xFF
            return f"""
    /**
     * Write {type_name} ({spec.comment})
     * {description}
     *
     * Converts float 0.0-1.0 to value 0-{max_val}.
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Number of bytes written (1)
     */
    public static int {method_name}(byte[] buffer, int offset, float value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        buffer[offset] = (byte) (Math.round(clamped * {max_val}.0f) & 0x{byte_mask:02X});
        return 1;
    }}
"""
        else:
            int_spec = spec.integer_spec
            if not int_spec:
                return ""

            lines: list[str] = []
            for i, (shift, mask) in enumerate(zip(int_spec.shifts, int_spec.masks, strict=True)):
                expr = (
                    f"(byte) (val & 0x{mask:02X})"
                    if shift == 0
                    else f"(byte) ((val >> {shift}) & 0x{mask:02X})"
                )
                lines.append(f"        buffer[offset + {i}] = {expr};")

            body = "\n".join(lines)

            return f"""
    /**
     * Write {type_name} ({spec.comment})
     * {description}
     *
     * Converts float 0.0-1.0 to uint16 0-{max_val}.
     *
     * @param buffer Output buffer
     * @param offset Write position in buffer
     * @param value Float value to encode (clamped to 0.0-1.0)
     * @return Number of bytes written ({spec.byte_count})
     */
    public static int {method_name}(byte[] buffer, int offset, float value) {{
        float clamped = Math.max(0.0f, Math.min(1.0f, value));
        int val = Math.round(clamped * {max_val}.0f) & 0xFFFF;
{body}
        return {spec.byte_count};
    }}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # String Encoder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_string_encoder(self, description: str) -> str:
        """Generate string encoder."""
        spec = self.strategy.get_string_spec()

        if self.backend.name == "cpp":
            return self._generate_cpp_string_encoder(spec, description)
        elif self.backend.name == "java":
            return self._generate_java_string_encoder(spec, description)
        return ""

    def _generate_cpp_string_encoder(
        self, spec: StringEncodingSpec, description: str
    ) -> str:
        """Generate C++ string encoder."""
        return f"""
/**
 * Encode string ({spec.comment})
 * {description}
 *
 * Format: [length] [char0] [char1] ... [charN-1]
 * Max length: {spec.max_length} chars
 */
static inline void encodeString(uint8_t*& buf, const std::string& str) {{
    uint8_t len = static_cast<uint8_t>(str.length()) & 0x{spec.length_mask:02X};
    *buf++ = len;

    for (size_t i = 0; i < len; ++i) {{
        *buf++ = static_cast<uint8_t>(str[i]) & 0x{spec.char_mask:02X};
    }}
}}
"""

    def _generate_java_string_encoder(
        self, spec: StringEncodingSpec, description: str
    ) -> str:
        """Generate Java string encoder."""
        return f"""
    /**
     * Write string ({spec.comment})
     * {description}
     *
     * Format: [length] [char0] [char1] ... [charN-1]
     * Max length: {spec.max_length} chars
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

        int len = Math.min(value.length(), Math.min(maxLength, {spec.max_length}));
        buffer[offset] = (byte) (len & 0x{spec.length_mask:02X});

        for (int i = 0; i < len; i++) {{
            buffer[offset + 1 + i] = (byte) (value.charAt(i) & 0x{spec.char_mask:02X});
        }}

        return 1 + len;
    }}
"""
