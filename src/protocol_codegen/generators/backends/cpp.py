"""
C++ Language Backend.

Implements LanguageBackend for C++ code generation.
Handles C++ syntax, STL types, and embedded-friendly patterns.

Uses TypeRegistry for type mappings (cpp_type field).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.generators.backends.base import LanguageBackend

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.common.encoding.operations import (
        DecoderMethodSpec,
        MethodSpec,
    )


class CppBackend(LanguageBackend):
    """C++ code generation backend.

    Generates C++17-compatible code with STL containers.
    Uses namespace 'Protocol' by default.
    """

    DEFAULT_NAMESPACE = "Protocol"

    def __init__(self, namespace: str | None = None):
        """Initialize C++ backend.

        Args:
            namespace: Namespace to use (default: 'Protocol')
        """
        self._namespace = namespace or self.DEFAULT_NAMESPACE

    @property
    def namespace(self) -> str:
        """Get the namespace for generated code."""
        return self._namespace

    # ─────────────────────────────────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "cpp"

    @property
    def file_extension(self) -> str:
        return ".hpp"

    # ─────────────────────────────────────────────────────────────────────────
    # Type Mapping
    # ─────────────────────────────────────────────────────────────────────────

    def get_type(self, type_name: str, registry: TypeRegistry) -> str:
        """Get C++ type from TypeRegistry.

        Falls back to type_name if not found (for custom types).
        """
        try:
            atomic_type = registry.get(type_name)
            if atomic_type.cpp_type:
                return atomic_type.cpp_type
        except KeyError:
            pass
        # Not a builtin - assume it's a custom type name (PascalCase)
        return type_name

    def array_type(self, element_type: str, size: int | None, dynamic: bool = False) -> str:
        """Generate C++ array type.

        - Fixed array: std::array<T, N>
        - Dynamic array: std::vector<T>
        """
        if dynamic or size is None:
            return f"std::vector<{element_type}>"
        return f"std::array<{element_type}, {size}>"

    def optional_type(self, inner_type: str) -> str:
        """Generate C++ optional type."""
        return f"std::optional<{inner_type}>"

    # ─────────────────────────────────────────────────────────────────────────
    # Include/Import Statements
    # ─────────────────────────────────────────────────────────────────────────

    def include_statement(self, path: str, is_system: bool = False) -> str:
        """Generate C++ #include statement.

        System includes use <...>, local includes use "..."
        """
        if is_system or path.startswith("<"):
            # Clean up if already has brackets
            clean_path = path.strip("<>")
            return f"#include <{clean_path}>"
        return f'#include "{path}"'

    # ─────────────────────────────────────────────────────────────────────────
    # Namespace Handling
    # ─────────────────────────────────────────────────────────────────────────

    def namespace_open(self, name: str) -> str:
        """Open C++ namespace."""
        return f"namespace {name} {{"

    def namespace_close(self, name: str) -> str:
        """Close C++ namespace with comment."""
        return f"}}  // namespace {name}"

    # ─────────────────────────────────────────────────────────────────────────
    # File Structure
    # ─────────────────────────────────────────────────────────────────────────

    def file_header(
        self,
        output_path: Path,
        description: str,
        includes: list[str] | None = None,
        namespace: str | None = None,
    ) -> str:
        """Generate C++ file header.

        Includes:
        - #pragma once
        - Auto-generated comment
        - #include directives
        - Namespace opening
        """
        lines: list[str] = []

        # Pragma once
        lines.append("#pragma once")
        lines.append("")

        # Auto-generated comment
        lines.append(self.auto_generated_comment(output_path.name))
        lines.append("")

        # Description (if provided and different from filename)
        if description:
            lines.append(f"// {description}")
            lines.append("")

        # Includes
        if includes:
            for inc in includes:
                is_system = inc.startswith("<") or inc.startswith("std")
                lines.append(self.include_statement(inc, is_system=is_system))
            lines.append("")

        # Namespace
        ns = namespace or self._namespace
        if ns:
            lines.append(self.namespace_open(ns))
            lines.append("")

        return "\n".join(lines)

    def file_footer(self, namespace: str | None = None) -> str:
        """Generate C++ file footer."""
        ns = namespace or self._namespace
        if ns:
            return f"\n{self.namespace_close(ns)}\n"
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Encoder/Decoder Idioms
    # ─────────────────────────────────────────────────────────────────────────

    def encode_call(self, method: str, value: str, buffer_var: str = "buf") -> str:
        """Generate C++ encoder call (static method)."""
        return f"Encoder::{method}({buffer_var}, {value});"

    def decode_call(self, method: str, buffer_var: str = "buf") -> str:
        """Generate C++ decoder call (static method)."""
        return f"Decoder::{method}({buffer_var})"

    # ─────────────────────────────────────────────────────────────────────────
    # Method Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def render_encoder_method(
        self,
        spec: MethodSpec,
        registry: TypeRegistry,
    ) -> str:
        """Render encoder method for C++."""
        cpp_type = self.get_type(spec.param_type, registry)
        method_name = f"encode{spec.method_name}"

        # Handle string specially
        if spec.type_name == "string":
            return self._render_cpp_string_encoder(spec)

        # Build body from byte writes
        body_lines: list[str] = []

        # Handle preamble
        if spec.preamble:
            if spec.preamble == "FLOAT_BITCAST":
                body_lines.append("uint32_t bits;")
                body_lines.append("memcpy(&bits, &val, sizeof(float));")
            elif spec.preamble.startswith("NORM_CLAMP"):
                body_lines.append("if (val < 0.0f) val = 0.0f;")
                body_lines.append("if (val > 1.0f) val = 1.0f;")
                # Extract scale from preamble
                parts = dict(p.split("=") for p in spec.preamble.split(";") if "=" in p)
                scale = parts.get("NORM_SCALE", "255")
                if spec.byte_count == 1:
                    body_lines.append(
                        f"uint8_t norm = static_cast<uint8_t>(val * {scale}.0f + 0.5f);"
                    )
                else:
                    body_lines.append(
                        f"uint16_t norm = static_cast<uint16_t>(val * {scale}.0f + 0.5f);"
                    )

        # Handle signed cast
        if spec.needs_signed_cast:
            unsigned_type = cpp_type.replace("int", "uint")
            body_lines.append(f"{unsigned_type} val = static_cast<{unsigned_type}>(value);")
            param_name = "value"
        else:
            param_name = "val"

        # Add byte writes
        for op in spec.byte_writes:
            body_lines.append(f"*buf++ = {op.expression};")

        # Build function
        body = "\n".join(f"    {line}" for line in body_lines)

        return f"""
/**
 * Encode {spec.type_name} ({spec.byte_count} byte{"s" if spec.byte_count != 1 else ""})
 * {spec.doc_comment}
 */
static inline void {method_name}(uint8_t*& buf, {cpp_type} {param_name}) {{
{body}
}}"""

    def _render_cpp_string_encoder(self, spec: MethodSpec) -> str:
        """Render C++ string encoder (special case)."""
        # Parse preamble for masks
        parts = dict(p.split("=") for p in spec.preamble.split(";") if "=" in p)
        length_mask = parts.get("LENGTH_MASK", "0xFF")
        char_mask = parts.get("CHAR_MASK", "0xFF")
        max_length = parts.get("MAX_LENGTH", "255")

        return f"""
/**
 * Encode string (variable length)
 * {spec.doc_comment}
 *
 * Format: [length] [char0] [char1] ... [charN-1]
 * Max length: {max_length} chars
 */
static inline void encodeString(uint8_t*& buf, const std::string& str) {{
    uint8_t len = static_cast<uint8_t>(str.length()) & {length_mask};
    *buf++ = len;

    for (size_t i = 0; i < len; ++i) {{
        *buf++ = static_cast<uint8_t>(str[i]) & {char_mask};
    }}
}}"""

    # ─────────────────────────────────────────────────────────────────────────
    # Decoder Method Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def render_decoder_method(
        self,
        spec: DecoderMethodSpec,
        registry: TypeRegistry,
    ) -> str:
        """Render decoder method for C++."""
        cpp_type = self.get_type(spec.result_type, registry)
        method_name = f"decode{spec.method_name}"

        # Handle string specially
        if spec.type_name == "string":
            return self._render_cpp_string_decoder(spec)

        # Build body
        body_lines: list[str] = []

        # Size check
        if spec.byte_count > 0:
            body_lines.append(f"if (remaining < {spec.byte_count}) return false;")
            body_lines.append("")

        # Bool is special case
        if spec.type_name == "bool":
            body_lines.append("out = (*buf++) != 0x00;")
            body_lines.append("remaining -= 1;")
            body_lines.append("return true;")
        elif spec.postamble and spec.postamble == "FLOAT_BITCAST":
            # Float: read bytes into bits, then memcpy
            self._build_cpp_byte_reads(spec, body_lines, "bits", "uint32_t")
            body_lines.append("memcpy(&out, &bits, sizeof(float));")
            body_lines.append(f"buf += {spec.byte_count};")
            body_lines.append(f"remaining -= {spec.byte_count};")
            body_lines.append("return true;")
        elif spec.postamble and spec.postamble.startswith("NORM_SCALE"):
            # Norm: read bytes, then scale to float
            parts = dict(p.split("=") for p in spec.postamble.split(";") if "=" in p)
            scale = parts.get("NORM_SCALE", "255")
            if spec.byte_count == 1:
                mask = spec.byte_reads[0].mask
                if mask:
                    body_lines.append(f"uint8_t raw = *buf++ & 0x{mask:02X};")
                else:
                    body_lines.append("uint8_t raw = *buf++;")
            else:
                self._build_cpp_byte_reads(spec, body_lines, "raw", "uint16_t")
                body_lines.append(f"buf += {spec.byte_count};")
            body_lines.append(f"out = static_cast<float>(raw) / {scale}.0f;")
            body_lines.append(f"remaining -= {spec.byte_count};")
            body_lines.append("return true;")
        else:
            # Integer types
            if spec.needs_signed_cast:
                unsigned_type = cpp_type.replace("int", "uint")
                self._build_cpp_byte_reads(spec, body_lines, "bits", unsigned_type)
                body_lines.append(f"out = static_cast<{cpp_type}>(bits);")
            else:
                self._build_cpp_byte_reads(spec, body_lines, "out", cpp_type)
            body_lines.append(f"buf += {spec.byte_count};")
            body_lines.append(f"remaining -= {spec.byte_count};")
            body_lines.append("return true;")

        body = "\n".join(f"    {line}" for line in body_lines)

        return f"""
/**
 * Decode {spec.type_name} ({spec.byte_count} byte{"s" if spec.byte_count != 1 else ""})
 * {spec.doc_comment}
 */
static inline bool {method_name}(
    const uint8_t*& buf, size_t& remaining, {cpp_type}& out) {{
{body}
}}"""

    def _build_cpp_byte_reads(
        self,
        spec: DecoderMethodSpec,
        body_lines: list[str],
        var_name: str,
        var_type: str,
    ) -> None:
        """Build C++ byte read expressions."""
        parts: list[str] = []
        for op in spec.byte_reads:
            expr = f"buf[{op.index}]"
            if op.mask:
                expr = f"({expr} & 0x{op.mask:02X})"
            if op.shift > 0:
                expr = f"(static_cast<{var_type}>({expr}) << {op.shift})"
            parts.append(expr)

        if len(parts) == 1:
            body_lines.append(f"{var_type} {var_name} = {parts[0]};")
        else:
            body_lines.append(f"{var_type} {var_name} = {parts[0]}")
            for part in parts[1:-1]:
                body_lines.append(f"    | {part}")
            body_lines.append(f"    | {parts[-1]};")

    def _render_cpp_string_decoder(self, spec: DecoderMethodSpec) -> str:
        """Render C++ string decoder (special case)."""
        parts = dict(p.split("=") for p in spec.postamble.split(";") if "=" in p)
        length_mask = parts.get("LENGTH_MASK", "0xFF")
        char_mask = parts.get("CHAR_MASK", "0xFF")
        max_length = parts.get("MAX_LENGTH", "255")

        return f"""
/**
 * Decode string (variable length)
 * {spec.doc_comment}
 *
 * Format: [length] [char0] [char1] ... [charN-1]
 * Max length: {max_length} chars
 */
static inline bool decodeString(
    const uint8_t*& buf, size_t& remaining, std::string& out) {{

    if (remaining < 1) return false;

    uint8_t len = *buf++ & {length_mask};
    remaining -= 1;

    if (remaining < len) return false;

    out.clear();
    out.reserve(len);
    for (uint8_t i = 0; i < len; ++i) {{
        out.push_back(static_cast<char>(*buf++ & {char_mask}));
    }}
    remaining -= len;
    return true;
}}"""

    # ─────────────────────────────────────────────────────────────────────────
    # C++ Specific Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def constexpr_constant(self, type_name: str, name: str, value: str) -> str:
        """Generate constexpr constant declaration.

        Args:
            type_name: C++ type (e.g., 'uint8_t')
            name: Constant name
            value: Constant value

        Returns:
            'static constexpr uint8_t NAME = 42;'
        """
        return f"static constexpr {type_name} {name} = {value};"

    def struct_field(self, type_name: str, field_name: str) -> str:
        """Generate struct field declaration.

        Args:
            type_name: C++ type
            field_name: Field name

        Returns:
            '    uint8_t fieldName;'
        """
        return f"    {type_name} {field_name};"

    def static_inline_function(
        self,
        return_type: str,
        name: str,
        params: list[tuple[str, str]],
        body_lines: list[str],
    ) -> str:
        """Generate static inline function.

        Args:
            return_type: Return type (e.g., 'void', 'uint8_t')
            name: Function name
            params: List of (type, name) tuples
            body_lines: Lines of function body

        Returns:
            Complete function definition
        """
        param_str = ", ".join(f"{t} {n}" for t, n in params)
        lines = [f"static inline {return_type} {name}({param_str}) {{"]
        for line in body_lines:
            lines.append(f"    {line}")
        lines.append("}")
        return "\n".join(lines)

    def standard_includes(self) -> list[str]:
        """Get standard includes for protocol code."""
        return ["<cstdint>", "<cstring>", "<string>", "<array>", "<vector>"]
