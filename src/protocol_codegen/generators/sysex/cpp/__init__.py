"""
C++ Code Generators for SysEx Protocol
Generates C++ protocol files (structs, MessageID, etc.)

Note: Encoder/Decoder generation now uses templates directly via:
  - EncoderTemplate(CppBackend(), SysExEncodingStrategy())
  - DecoderTemplate(CppBackend(), SysExEncodingStrategy())
"""

from protocol_codegen.generators.common.cpp import (
    generate_enum_hpp,
    generate_message_structure_hpp,
    generate_messageid_hpp,
    generate_protocol_callbacks_hpp,
    generate_protocol_methods_hpp,
)

from .constants_generator import generate_constants_hpp
from .decoder_registry_generator import generate_decoder_registry_hpp
from .protocol_generator import generate_protocol_template_hpp
from .struct_generator import generate_struct_hpp

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
