"""
Code Generation Templates.

This package provides template classes that combine LanguageBackend and EncodingStrategy
to generate protocol-specific code for different target languages.

Templates:
- EncoderTemplate: Generates Encoder.hpp/Encoder.java files
- DecoderTemplate: Generates Decoder.hpp/Decoder.java files

Usage:
    from protocol_codegen.generators.languages.cpp import CppBackend
    from protocol_codegen.generators.protocols.binary import BinaryEncodingStrategy
    from protocol_codegen.generators.templates import EncoderTemplate, DecoderTemplate

    encoder = EncoderTemplate(CppBackend(), BinaryEncodingStrategy())
    decoder = DecoderTemplate(CppBackend(), BinaryEncodingStrategy())
"""

from .decoder import DecoderTemplate
from .encoder import EncoderTemplate

__all__ = [
    "DecoderTemplate",
    "EncoderTemplate",
]
