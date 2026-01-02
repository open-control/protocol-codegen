"""
Code Generation Templates.

This package provides template classes that combine LanguageBackend and EncodingStrategy
to generate protocol-specific code for different target languages.

Templates:
- EncoderTemplate: Generates Encoder.hpp/Encoder.java files
- DecoderTemplate: Generates Decoder.hpp/Decoder.java files

Usage:
    from protocol_codegen.generators.backends import CppBackend
    from protocol_codegen.generators.protocols.serial8 import Serial8EncodingStrategy
    from protocol_codegen.generators.templates import EncoderTemplate, DecoderTemplate

    encoder = EncoderTemplate(CppBackend(), Serial8EncodingStrategy())
    decoder = DecoderTemplate(CppBackend(), Serial8EncodingStrategy())
"""

from .decoder import DecoderTemplate
from .encoder import EncoderTemplate

__all__ = [
    "DecoderTemplate",
    "EncoderTemplate",
]
