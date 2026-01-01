"""
Encoder Template for generating Encoder.hpp/Encoder.java files.

Combines LanguageBackend (syntax) with EncodingStrategy (encoding logic)
to generate protocol-specific encoder code for any target language.

Uses TypeEncoders to produce MethodSpecs, then delegates rendering
to the LanguageBackend.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.generators.common.type_encoders import (
    BoolEncoder,
    FloatEncoder,
    IntegerEncoder,
    NormEncoder,
    StringEncoder,
    TypeEncoder,
)

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class EncoderTemplate:
    """Template for generating Encoder files.

    Generates complete encoder files for any combination of:
    - LanguageBackend: C++, Java, (future: Rust, Python, etc.)
    - EncodingStrategy: Serial8 (8-bit), SysEx (7-bit)

    Uses TypeEncoders to produce MethodSpecs (language-agnostic encoding
    specifications), then calls backend.render_encoder_method() for
    language-specific rendering.
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

        # Create type encoders with the encoding strategy
        self._type_encoders: list[TypeEncoder] = [
            BoolEncoder(strategy),
            IntegerEncoder(strategy),
            FloatEncoder(strategy),
            NormEncoder(strategy),
            StringEncoder(strategy),
        ]

        # Build type -> encoder mapping for fast lookup
        self._encoder_map: dict[str, TypeEncoder] = {}
        for encoder in self._type_encoders:
            for type_name in encoder.supported_types():
                self._encoder_map[type_name] = encoder

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
        """Generate all encoder methods using TypeEncoders.

        For each builtin type in the registry:
        1. Find the appropriate TypeEncoder
        2. Get a MethodSpec from the encoder
        3. Render to language-specific code via backend
        """
        encoders: list[str] = []

        for type_name, atomic_type in sorted(type_registry.types.items()):
            if not atomic_type.is_builtin:
                continue

            encoder = self._encoder_map.get(type_name)
            if not encoder:
                continue

            # Get language-agnostic method specification
            spec = encoder.get_method_spec(type_name, atomic_type.description)

            # Render to language-specific code
            code = self.backend.render_encoder_method(spec, type_registry)
            if code:
                encoders.append(code)

        return "\n".join(encoders)
