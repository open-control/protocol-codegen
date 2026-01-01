"""
Java Language Backend.

Implements LanguageBackend for Java code generation.
Handles Java syntax, package structure, and Android compatibility.

Uses TypeRegistry for type mappings (java_type field).
Note: Java has no unsigned types, so unsigned integers use larger signed types.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.generators.backends.base import LanguageBackend

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.common.encoding.operations import MethodSpec


class JavaBackend(LanguageBackend):
    """Java code generation backend.

    Generates Java 8+ compatible code.
    Uses package structure and nullable references for optionals.
    """

    DEFAULT_PACKAGE = "protocol"

    def __init__(self, package: str | None = None):
        """Initialize Java backend.

        Args:
            package: Java package name (default: 'protocol')
        """
        self._package = package or self.DEFAULT_PACKAGE

    @property
    def package(self) -> str:
        """Get the package for generated code."""
        return self._package

    # ─────────────────────────────────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "java"

    @property
    def file_extension(self) -> str:
        return ".java"

    # ─────────────────────────────────────────────────────────────────────────
    # Type Mapping
    # ─────────────────────────────────────────────────────────────────────────

    def get_type(self, type_name: str, registry: TypeRegistry) -> str:
        """Get Java type from TypeRegistry.

        Falls back to type_name if not found (for custom types).
        """
        try:
            atomic_type = registry.get(type_name)
            if atomic_type.java_type:
                return atomic_type.java_type
        except KeyError:
            pass
        # Not a builtin - assume it's a custom type name (PascalCase)
        return type_name

    def array_type(self, element_type: str, size: int | None, dynamic: bool = False) -> str:
        """Generate Java array type.

        Java uses simple array syntax for both fixed and dynamic.
        For dynamic lists, consider using ArrayList in specific cases.
        """
        return f"{element_type}[]"

    def optional_type(self, inner_type: str) -> str:
        """Generate Java optional type.

        Java uses nullable references, so we return the type as-is.
        For primitive types, use boxed versions if truly optional.
        """
        return inner_type

    # ─────────────────────────────────────────────────────────────────────────
    # Include/Import Statements
    # ─────────────────────────────────────────────────────────────────────────

    def include_statement(self, path: str, is_system: bool = False) -> str:
        """Generate Java import statement.

        Note: is_system is ignored in Java (all imports use same syntax).
        """
        # Clean up if already has semicolon
        clean_path = path.rstrip(";")
        return f"import {clean_path};"

    # ─────────────────────────────────────────────────────────────────────────
    # Package Handling
    # ─────────────────────────────────────────────────────────────────────────

    def namespace_open(self, name: str) -> str:
        """Generate Java package declaration.

        Note: Package declaration is at file start, not a scope opener.
        """
        return f"package {name};"

    def namespace_close(self, name: str) -> str:
        """Java doesn't close packages (no-op)."""
        return ""

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
        """Generate Java file header.

        Includes:
        - Package declaration
        - Auto-generated comment
        - Import statements
        """
        lines: list[str] = []

        # Package declaration (namespace in Java terms)
        pkg = namespace or self._package
        if pkg:
            lines.append(self.namespace_open(pkg))
            lines.append("")

        # Auto-generated comment
        lines.append(self.auto_generated_comment(output_path.name))
        lines.append("")

        # Description (if provided)
        if description:
            lines.append(f"// {description}")
            lines.append("")

        # Imports
        if includes:
            for imp in includes:
                lines.append(self.include_statement(imp))
            lines.append("")

        return "\n".join(lines)

    def file_footer(self, namespace: str | None = None) -> str:
        """Generate Java file footer.

        Java classes close with their own braces, not package-level.
        """
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Encoder/Decoder Idioms
    # ─────────────────────────────────────────────────────────────────────────

    def encode_call(self, method: str, value: str, buffer_var: str = "buffer") -> str:
        """Generate Java encoder call (static method)."""
        return f"Encoder.{method}({buffer_var}, {value});"

    def decode_call(self, method: str, buffer_var: str = "buffer") -> str:
        """Generate Java decoder call (static method)."""
        return f"Decoder.{method}({buffer_var})"

    # ─────────────────────────────────────────────────────────────────────────
    # Method Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def render_encoder_method(
        self,
        spec: MethodSpec,
        registry: TypeRegistry,
    ) -> str:
        """Render encoder method for Java."""
        java_type = self.get_type(spec.param_type, registry)
        method_name = f"write{spec.method_name}"

        # Handle string specially
        if spec.type_name == "string":
            return self._render_java_string_encoder(spec)

        # Build body from byte writes
        body_lines: list[str] = []

        # Handle preamble
        if spec.preamble:
            if spec.preamble == "FLOAT_BITCAST":
                body_lines.append("int bits = Float.floatToIntBits(val);")
            elif spec.preamble.startswith("NORM_CLAMP"):
                body_lines.append("if (val < 0.0f) val = 0.0f;")
                body_lines.append("if (val > 1.0f) val = 1.0f;")
                # Extract scale from preamble
                parts = dict(p.split("=") for p in spec.preamble.split(";") if "=" in p)
                scale = parts.get("NORM_SCALE", "255")
                body_lines.append(f"int norm = (int)(val * {scale}.0f + 0.5f);")

        # Handle signed cast for multi-byte
        if spec.needs_signed_cast:
            body_lines.append("int val = value & 0xFFFF;")
            param_name = "value"
        else:
            param_name = "val"

        # Add byte writes
        for op in spec.byte_writes:
            body_lines.append(f"buffer[offset + {op.index}] = (byte)({op.expression});")

        # Return byte count
        body_lines.append(f"return {spec.byte_count};")

        # Build method
        body = "\n".join(f"        {line}" for line in body_lines)

        return f"""
    /**
     * Write {spec.type_name} ({spec.byte_count} byte{"s" if spec.byte_count != 1 else ""})
     * {spec.doc_comment}
     * @return number of bytes written
     */
    public static int {method_name}(byte[] buffer, int offset, {java_type} {param_name}) {{
{body}
    }}"""

    def _render_java_string_encoder(self, spec: MethodSpec) -> str:
        """Render Java string encoder (special case)."""
        # Parse preamble for masks
        parts = dict(p.split("=") for p in spec.preamble.split(";") if "=" in p)
        length_mask = parts.get("LENGTH_MASK", "0xFF")
        char_mask = parts.get("CHAR_MASK", "0xFF")
        max_length = parts.get("MAX_LENGTH", "255")

        return f"""
    /**
     * Write string (variable length)
     * {spec.doc_comment}
     *
     * Format: [length] [char0] [char1] ... [charN-1]
     * Max length: {max_length} chars
     * @return number of bytes written
     */
    public static int writeString(byte[] buffer, int offset, String str) {{
        int len = Math.min(str.length(), {max_length}) & {length_mask};
        buffer[offset] = (byte)len;

        for (int i = 0; i < len; i++) {{
            buffer[offset + 1 + i] = (byte)(str.charAt(i) & {char_mask});
        }}
        return 1 + len;
    }}"""

    # ─────────────────────────────────────────────────────────────────────────
    # Java Specific Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def constant(self, type_name: str, name: str, value: str, visibility: str = "public") -> str:
        """Generate Java constant declaration.

        Args:
            type_name: Java type (e.g., 'int', 'byte')
            name: Constant name (UPPER_CASE recommended)
            value: Constant value
            visibility: 'public', 'private', 'protected', or 'package'

        Returns:
            'public static final int NAME = 42;'
        """
        vis = "" if visibility == "package" else f"{visibility} "
        return f"{vis}static final {type_name} {name} = {value};"

    def class_field(
        self,
        type_name: str,
        field_name: str,
        visibility: str = "private",
        is_final: bool = False,
    ) -> str:
        """Generate Java class field declaration.

        Args:
            type_name: Java type
            field_name: Field name (camelCase)
            visibility: Field visibility
            is_final: If True, add 'final' modifier

        Returns:
            '    private final int fieldName;'
        """
        vis = "" if visibility == "package" else f"{visibility} "
        final = "final " if is_final else ""
        return f"    {vis}{final}{type_name} {field_name};"

    def static_method(
        self,
        return_type: str,
        name: str,
        params: list[tuple[str, str]],
        body_lines: list[str],
        visibility: str = "public",
    ) -> str:
        """Generate static method.

        Args:
            return_type: Return type (e.g., 'void', 'int')
            name: Method name (camelCase)
            params: List of (type, name) tuples
            body_lines: Lines of method body
            visibility: Method visibility

        Returns:
            Complete method definition
        """
        vis = "" if visibility == "package" else f"{visibility} "
        param_str = ", ".join(f"{t} {n}" for t, n in params)
        lines = [f"    {vis}static {return_type} {name}({param_str}) {{"]
        for line in body_lines:
            lines.append(f"        {line}")
        lines.append("    }")
        return "\n".join(lines)

    def class_declaration(
        self,
        name: str,
        visibility: str = "public",
        is_final: bool = True,
    ) -> str:
        """Generate class declaration opening.

        Args:
            name: Class name (PascalCase)
            visibility: Class visibility
            is_final: If True, add 'final' modifier

        Returns:
            'public final class ClassName {'
        """
        vis = "" if visibility == "package" else f"{visibility} "
        final = "final " if is_final else ""
        return f"{vis}{final}class {name} {{"

    def standard_imports(self) -> list[str]:
        """Get standard imports for protocol code."""
        return ["java.nio.ByteBuffer", "java.nio.ByteOrder"]

    def boxed_type(self, primitive_type: str) -> str:
        """Get boxed type for primitive.

        Args:
            primitive_type: Primitive type (e.g., 'int', 'boolean')

        Returns:
            Boxed type (e.g., 'Integer', 'Boolean')
        """
        mapping = {
            "int": "Integer",
            "long": "Long",
            "short": "Short",
            "byte": "Byte",
            "float": "Float",
            "double": "Double",
            "boolean": "Boolean",
            "char": "Character",
        }
        return mapping.get(primitive_type, primitive_type)
