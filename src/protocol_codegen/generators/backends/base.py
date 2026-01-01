"""
Language Backend Abstract Base Class.

Defines the interface for language-specific code generation.
Each backend encapsulates syntax, idioms, and conventions for one target language.

The backend does NOT duplicate type mappings - those are in TypeRegistry.
Instead, it provides:
- File structure (headers, footers, extensions)
- Include/import syntax
- Namespace/package handling
- Array and optional type wrappers
- Encoder/decoder call patterns
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.common.encoding.operations import MethodSpec


class LanguageBackend(ABC):
    """Abstract base for language-specific code generation.

    Backends encapsulate language-specific syntax and conventions.
    Type mappings are delegated to TypeRegistry.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Language identifier: 'cpp', 'java', 'rust', etc."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension including dot: '.hpp', '.java', '.rs', etc."""
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Type Mapping (delegated to TypeRegistry)
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_type(self, type_name: str, registry: TypeRegistry) -> str:
        """Get language-specific type for a protocol type.

        Uses TypeRegistry to look up cpp_type or java_type.

        Args:
            type_name: Protocol type name (e.g., 'uint8', 'float32')
            registry: TypeRegistry with type definitions

        Returns:
            Language-specific type (e.g., 'uint8_t' for C++, 'int' for Java)
        """
        ...

    @abstractmethod
    def array_type(self, element_type: str, size: int | None, dynamic: bool = False) -> str:
        """Generate array type declaration.

        Args:
            element_type: The element type (already language-specific)
            size: Fixed array size, or None for dynamic
            dynamic: If True, use dynamic container (vector/ArrayList)

        Returns:
            Array type: 'std::array<T, N>' (C++), 'T[]' (Java), etc.
        """
        ...

    @abstractmethod
    def optional_type(self, inner_type: str) -> str:
        """Generate optional type wrapper.

        Args:
            inner_type: The wrapped type (already language-specific)

        Returns:
            Optional type: 'std::optional<T>' (C++), 'T' (Java nullable), etc.
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Include/Import Statements
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def include_statement(self, path: str, is_system: bool = False) -> str:
        """Generate include/import statement.

        Args:
            path: Include path or import name
            is_system: If True, use system include (<...>) vs local ("...")

        Returns:
            Include/import line: '#include <path>' or 'import path;'
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Namespace/Package Handling
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def namespace_open(self, name: str) -> str:
        """Open namespace/package scope.

        Args:
            name: Namespace/package name

        Returns:
            Opening statement: 'namespace Foo {' or 'package foo;'
        """
        ...

    @abstractmethod
    def namespace_close(self, name: str) -> str:
        """Close namespace/package scope.

        Args:
            name: Namespace/package name (for closing comment)

        Returns:
            Closing statement: '}  // namespace Foo' or '' (Java)
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # File Structure
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def file_header(
        self,
        output_path: Path,
        description: str,
        includes: list[str] | None = None,
        namespace: str | None = None,
    ) -> str:
        """Generate complete file header.

        Args:
            output_path: Output file path (for header comment)
            description: File description
            includes: List of includes/imports
            namespace: Optional namespace/package name

        Returns:
            Complete header with pragma, comment, includes, namespace
        """
        ...

    @abstractmethod
    def file_footer(self, namespace: str | None = None) -> str:
        """Generate file footer.

        Args:
            namespace: Namespace to close (if any)

        Returns:
            Footer with closing braces, namespace comment, etc.
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Encoder/Decoder Idioms
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def encode_call(self, method: str, value: str, buffer_var: str = "buf") -> str:
        """Generate encoder method call.

        Args:
            method: Encoder method name (e.g., 'encodeUint8')
            value: Value expression to encode
            buffer_var: Buffer variable name

        Returns:
            Encoder call: 'Encoder::encodeUint8(buf, val);' (C++)
                         'Encoder.encodeUint8(buffer, val);' (Java)
        """
        ...

    @abstractmethod
    def decode_call(self, method: str, buffer_var: str = "buf") -> str:
        """Generate decoder method call.

        Args:
            method: Decoder method name (e.g., 'decodeUint8')
            buffer_var: Buffer variable name

        Returns:
            Decoder call: 'Decoder::decodeUint8(buf)' (C++)
                         'Decoder.decodeUint8(buffer)' (Java)
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Method Rendering
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def render_encoder_method(
        self,
        spec: MethodSpec,
        registry: TypeRegistry,
    ) -> str:
        """Render a MethodSpec to language-specific encoder code.

        This is the main entry point for generating encoder methods.
        The MethodSpec contains language-agnostic encoding logic,
        and this method translates it to concrete syntax.

        Args:
            spec: Language-agnostic method specification
            registry: Type registry for type mapping

        Returns:
            Complete encoder method as string
        """
        ...

    # ─────────────────────────────────────────────────────────────────────────
    # Comment Generation
    # ─────────────────────────────────────────────────────────────────────────

    def auto_generated_comment(self, filename: str) -> str:
        """Generate auto-generated file comment.

        Default implementation using C-style comments.
        Override if needed for different comment syntax.

        Args:
            filename: Name of the generated file

        Returns:
            Multi-line comment block
        """
        return f"""/**
 * {filename}
 *
 * AUTO-GENERATED - DO NOT EDIT
 */"""

    def doc_comment(self, description: str) -> str:
        """Generate documentation comment.

        Default implementation using C-style doc comments.

        Args:
            description: Description text

        Returns:
            Doc comment block
        """
        return f"/** {description} */"

    # ─────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────

    def generate_filename(self, base_name: str) -> str:
        """Generate output filename with correct extension.

        Args:
            base_name: Base name without extension

        Returns:
            Filename with extension
        """
        return f"{base_name}{self.file_extension}"
