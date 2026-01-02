"""
Decoder Template for generating Decoder.hpp/Decoder.java files.

Combines LanguageBackend (syntax) with EncodingStrategy (decoding logic)
to generate protocol-specific decoder code for any target language.

Uses TypeDecoders to produce DecoderMethodSpecs, then delegates rendering
to the LanguageBackend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.type_decoders import (
    BoolDecoder,
    FloatDecoder,
    IntegerDecoder,
    NormDecoder,
    StringDecoder,
    TypeDecoder,
)
from protocol_codegen.generators.templates.base import CodecTemplate

if TYPE_CHECKING:
    from protocol_codegen.core.loader import TypeRegistry


class DecoderTemplate(CodecTemplate):
    """Template for generating Decoder files.

    Generates complete decoder files for any combination of:
    - LanguageBackend: C++, Java, (future: Rust, Python, etc.)
    - EncodingStrategy: Serial8 (8-bit), SysEx (7-bit)

    Uses TypeDecoders to produce DecoderMethodSpecs (language-agnostic decoding
    specifications), then calls backend.render_decoder_method() for
    language-specific rendering.
    """

    @property
    def codec_name(self) -> str:
        """Return 'Decoder'."""
        return "Decoder"

    @property
    def cpp_extra_includes(self) -> list[str]:
        """Decoder needs cstddef for size_t."""
        return ["<cstddef>"]

    def _build_handler_map(self) -> dict[str, TypeDecoder]:
        """Build type -> decoder mapping."""
        type_decoders: list[TypeDecoder] = [
            BoolDecoder(self.strategy),
            IntegerDecoder(self.strategy),
            FloatDecoder(self.strategy),
            NormDecoder(self.strategy),
            StringDecoder(self.strategy),
        ]

        decoder_map: dict[str, TypeDecoder] = {}
        for decoder in type_decoders:
            for type_name in decoder.supported_types():
                decoder_map[type_name] = decoder

        return decoder_map

    def _generate_methods(self, type_registry: TypeRegistry) -> str:
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

            decoder = self._handler_map.get(type_name)
            if not decoder:
                continue

            # Get language-agnostic method specification
            spec = decoder.get_method_spec(type_name, atomic_type.description)

            # Render to language-specific code
            code = self.backend.render_decoder_method(spec, type_registry)
            if code:
                decoders.append(code)

        return "\n".join(decoders)
