"""
C++ Code Generators for Serial8 Protocol
Generates C++ protocol files with 8-bit binary encoding.

Note: Encoder/Decoder generation now uses templates directly via:
  - EncoderTemplate(CppBackend(), Serial8EncodingStrategy())
  - DecoderTemplate(CppBackend(), Serial8EncodingStrategy())
"""

from protocol_codegen.generators.common.cpp import (
    generate_decoder_registry_hpp,
    generate_enum_hpp,
    generate_message_structure_hpp,
    generate_messageid_hpp,
    generate_protocol_callbacks_hpp,
    generate_protocol_methods_hpp,
    generate_struct_hpp,
)

from .constants_generator import generate_constants_hpp
from .protocol_generator import generate_protocol_template_hpp

__all__ = [
    "generate_constants_hpp",
    "generate_decoder_registry_hpp",
    "generate_enum_hpp",
    "generate_message_structure_hpp",
    "generate_messageid_hpp",
    "generate_protocol_callbacks_hpp",
    "generate_protocol_methods_hpp",
    "generate_protocol_template_hpp",
    "generate_struct_hpp",
]
