"""
Encoder Template for generating Encoder.hpp/Encoder.java files.

Combines LanguageBackend (syntax) with EncodingStrategy (encoding logic)
to generate protocol-specific encoder code for any target language.

Uses TypeEncoders to produce MethodSpecs, then delegates rendering
to the LanguageBackend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.type_encoders import (
    BoolEncoder,
    FloatEncoder,
    IntegerEncoder,
    NormEncoder,
    StringEncoder,
    TypeEncoder,
)
from protocol_codegen.generators.templates.base import CodecTemplate

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry


class EncoderTemplate(CodecTemplate):
    """Template for generating Encoder files.

    Generates complete encoder files for any combination of:
    - LanguageBackend: C++, Java, (future: Rust, Python, etc.)
    - EncodingStrategy: Serial8 (8-bit), SysEx (7-bit)

    Uses TypeEncoders to produce MethodSpecs (language-agnostic encoding
    specifications), then calls backend.render_encoder_method() for
    language-specific rendering.
    """

    _handler_map: dict[str, TypeEncoder]

    @property
    def codec_name(self) -> str:
        """Return 'Encoder'."""
        return "Encoder"

    def _build_handler_map(self) -> dict[str, TypeEncoder]:
        """Build type -> encoder mapping."""
        type_encoders: list[TypeEncoder] = [
            BoolEncoder(self.strategy),
            IntegerEncoder(self.strategy),
            FloatEncoder(self.strategy),
            NormEncoder(self.strategy),
            StringEncoder(self.strategy),
        ]

        encoder_map: dict[str, TypeEncoder] = {}
        for encoder in type_encoders:
            for type_name in encoder.supported_types():
                encoder_map[type_name] = encoder

        return encoder_map

    def _generate_methods(self, type_registry: TypeRegistry) -> str:
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

            encoder = self._handler_map.get(type_name)
            if not encoder:
                continue

            # Get language-agnostic method specification
            spec = encoder.get_method_spec(type_name, atomic_type.description)

            # Render to language-specific code
            code = self.backend.render_encoder_method(spec, type_registry)
            if code:
                encoders.append(code)

        return "\n".join(encoders)
