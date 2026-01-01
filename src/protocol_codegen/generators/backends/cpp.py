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
