"""
Code Generation Templates.

This package provides template classes that combine LanguageBackend and EncodingStrategy
to generate protocol-specific code for different target languages.

Templates:
- EncoderTemplate: Generates Encoder.hpp/Encoder.java files

Usage:
    from protocol_codegen.generators.backends import CppBackend
    from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy
    from protocol_codegen.generators.templates import EncoderTemplate

    template = EncoderTemplate(CppBackend(), Serial8EncodingStrategy())
    code = template.generate(type_registry, output_path)
"""

from .encoder import EncoderTemplate

__all__ = [
    "EncoderTemplate",
]
