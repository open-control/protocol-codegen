"""
Java Code Generators for SysEx Protocol
Generates Java protocol files for 7-bit MIDI SysEx.

Note: Protocol template generation now uses:
  - SysExJavaProtocolRenderer from renderers/protocol/

Note: Encoder/Decoder generation now uses templates directly via:
  - EncoderTemplate(JavaBackend(package=pkg), SysExEncodingStrategy())
  - DecoderTemplate(JavaBackend(package=pkg), SysExEncodingStrategy())
"""

from protocol_codegen.generators.common.java import (
    generate_constants_java,
    generate_decoder_registry_java,
    generate_enum_java,
    generate_messageid_java,
    generate_protocol_callbacks_java,
    generate_protocol_methods_java,
    generate_struct_java,
)

from .message_structure_generator import generate_message_structure_java

__all__ = [
    "generate_constants_java",
    "generate_decoder_registry_java",
    "generate_enum_java",
    "generate_message_structure_java",
    "generate_messageid_java",
    "generate_protocol_callbacks_java",
    "generate_protocol_methods_java",
    "generate_struct_java",
]
