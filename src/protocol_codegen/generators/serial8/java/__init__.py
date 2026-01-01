"""
Java Code Generators for Serial8 Protocol
Generates Java protocol files with 8-bit binary encoding.

Note: Encoder/Decoder generation now uses templates directly via:
  - EncoderTemplate(JavaBackend(package=pkg), Serial8EncodingStrategy())
  - DecoderTemplate(JavaBackend(package=pkg), Serial8EncodingStrategy())
"""

from protocol_codegen.generators.common.java import (
    generate_decoder_registry_java,
    generate_enum_java,
    generate_messageid_java,
    generate_protocol_callbacks_java,
    generate_protocol_methods_java,
    generate_struct_java,
)

from .constants_generator import generate_constants_java
from .protocol_generator import generate_protocol_template_java

__all__ = [
    "generate_constants_java",
    "generate_decoder_registry_java",
    "generate_enum_java",
    "generate_messageid_java",
    "generate_protocol_callbacks_java",
    "generate_protocol_methods_java",
    "generate_protocol_template_java",
    "generate_struct_java",
]
