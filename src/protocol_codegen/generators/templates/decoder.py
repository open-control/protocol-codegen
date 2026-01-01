"""
Decoder Template for generating Decoder.hpp/Decoder.java files.

Combines LanguageBackend (syntax) with EncodingStrategy (decoding logic)
to generate protocol-specific decoder code for any target language.

Uses TypeDecoders to produce DecoderMethodSpecs, then delegates rendering
to the LanguageBackend.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.generators.common.type_decoders import (
    BoolDecoder,
    FloatDecoder,
    IntegerDecoder,
    NormDecoder,
    StringDecoder,
    TypeDecoder,
)

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.generators.backends.base import LanguageBackend
    from protocol_codegen.generators.common.encoding import EncodingStrategy


class DecoderTemplate:
    """Template for generating Decoder files.

    Generates complete decoder files for any combination of:
    - LanguageBackend: C++, Java, (future: Rust, Python, etc.)
    - EncodingStrategy: Serial8 (8-bit), SysEx (7-bit)

    Uses TypeDecoders to produce DecoderMethodSpecs (language-agnostic decoding
    specifications), then calls backend.render_decoder_method() for
    language-specific rendering.
    """

    def __init__(
        self,
        backend: LanguageBackend,
        strategy: EncodingStrategy,
    ):
        """Initialize decoder template.

        Args:
            backend: Language backend for syntax
            strategy: Encoding strategy for protocol-specific logic
        """
        self.backend = backend
        self.strategy = strategy

        # Create type decoders with the encoding strategy
        self._type_decoders: list[TypeDecoder] = [
            BoolDecoder(strategy),
            IntegerDecoder(strategy),
            FloatDecoder(strategy),
            NormDecoder(strategy),
            StringDecoder(strategy),
        ]

        # Build type -> decoder mapping for fast lookup
        self._decoder_map: dict[str, TypeDecoder] = {}
        for decoder in self._type_decoders:
            for type_name in decoder.supported_types():
                self._decoder_map[type_name] = decoder

    def generate(self, type_registry: TypeRegistry, output_path: Path) -> str:
        """Generate complete decoder file.

        Args:
            type_registry: Registry with builtin types
            output_path: Output file path (for header comment)

        Returns:
            Complete decoder file content
        """
        parts = [
            self._generate_header(output_path),
            self._generate_class_open(),
            self._generate_decoders(type_registry),
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

// {self.strategy.name} Decoder - {self.strategy.description}

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>

namespace Protocol {{
"""

    def _generate_java_header(self, output_path: Path) -> str:
        """Generate Java header."""
        package = getattr(self.backend, "package", "protocol")
        return f"""package {package};

{self.backend.auto_generated_comment(output_path.name)}

// {self.strategy.name} Decoder - {self.strategy.description}

"""

    def _generate_class_open(self) -> str:
        """Generate class/struct opening."""
        if self.backend.name == "cpp":
            return "struct Decoder {"
        elif self.backend.name == "java":
            return "public final class Decoder {"
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

    def _generate_decoders(self, type_registry: TypeRegistry) -> str:
        """Generate all decoder methods using TypeDecoders.

        For each builtin type in the registry:
        1. Find the appropriate TypeDecoder
        2. Get a DecoderMethodSpec from the decoder
        3. Render to language-specific code via backend
        """
        decoders: list[str] = []

        for type_name, atomic_type in sorted(type_registry.types.items()):
            if not atomic_type.is_builtin:
                continue

            decoder = self._decoder_map.get(type_name)
            if not decoder:
                continue

            # Get language-agnostic method specification
            spec = decoder.get_method_spec(type_name, atomic_type.description)

            # Render to language-specific code
            code = self.backend.render_decoder_method(spec, type_registry)
            if code:
                decoders.append(code)

        return "\n".join(decoders)
