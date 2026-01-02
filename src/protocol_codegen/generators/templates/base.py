"""
Base Codec Template for generating Encoder/Decoder files.

Provides common structure for EncoderTemplate and DecoderTemplate,
eliminating code duplication while maintaining clear separation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class CodecTemplate(ABC):
    """Abstract base class for Encoder/Decoder templates.

    Provides common file generation structure:
    - Header with includes/imports
    - Class/struct opening
    - Type-specific methods (encode/decode)
    - Class/struct closing
    - Footer

    Subclasses implement:
    - _get_type_handlers(): Return list of TypeEncoder/TypeDecoder instances
    - _build_handler_map(): Build type -> handler mapping
    - _generate_methods(): Generate all encoder/decoder methods
    - codec_name: Property returning "Encoder" or "Decoder"
    - cpp_extra_includes: Property for additional C++ includes
    """

    def __init__(
        self,
        backend: LanguageBackend,
        strategy: EncodingStrategy,
    ):
        """Initialize codec template.

        Args:
            backend: Language backend for syntax
            strategy: Encoding strategy for protocol-specific logic
        """
        self.backend = backend
        self.strategy = strategy
        self._handler_map = self._build_handler_map()

    @property
    @abstractmethod
    def codec_name(self) -> str:
        """Return 'Encoder' or 'Decoder'."""
        ...

    @property
    def cpp_extra_includes(self) -> list[str]:
        """Return additional C++ includes needed by this codec."""
        return []

    @abstractmethod
    def _build_handler_map(self) -> dict:
        """Build type -> handler mapping."""
        ...

    @abstractmethod
    def _generate_methods(self, type_registry: TypeRegistry) -> str:
        """Generate all codec methods."""
        ...

    def generate(self, type_registry: TypeRegistry, output_path: Path) -> str:
        """Generate complete codec file.

        Args:
            type_registry: Registry with builtin types
            output_path: Output file path (for header comment)

        Returns:
            Complete encoder/decoder file content
        """
        parts = [
            self._generate_header(output_path),
            self._generate_class_open(),
            self._generate_methods(type_registry),
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
        includes = ["<cstdint>", "<cstring>", "<string>"] + self.cpp_extra_includes
        includes_str = "\n".join(f"#include {inc}" for inc in includes)

        return f"""#pragma once

{self.backend.auto_generated_comment(output_path.name)}

// {self.strategy.name} {self.codec_name} - {self.strategy.description}

{includes_str}

namespace Protocol {{
"""

    def _generate_java_header(self, output_path: Path) -> str:
        """Generate Java header."""
        package = getattr(self.backend, "package", "protocol")
        return f"""package {package};

{self.backend.auto_generated_comment(output_path.name)}

// {self.strategy.name} {self.codec_name} - {self.strategy.description}

"""

    def _generate_class_open(self) -> str:
        """Generate class/struct opening."""
        if self.backend.name == "cpp":
            return f"struct {self.codec_name} {{"
        elif self.backend.name == "java":
            return f"public final class {self.codec_name} {{"
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


__all__ = ["CodecTemplate"]
