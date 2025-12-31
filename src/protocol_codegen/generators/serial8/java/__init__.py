"""
Java Code Generators for Serial8 Protocol
Generates Java protocol files with 8-bit binary encoding.
"""

from protocol_codegen.generators.common.java import (
    generate_decoder_registry_java,
    generate_messageid_java,
    generate_protocol_callbacks_java,
)

from .constants_generator import generate_constants_java
from .decoder_generator import generate_decoder_java
from .encoder_generator import generate_encoder_java
from protocol_codegen.generators.common.java import generate_enum_java
from protocol_codegen.generators.common.java import generate_log_method
from protocol_codegen.generators.common.java import generate_protocol_methods_java
from .protocol_generator import generate_protocol_template_java
from .struct_generator import generate_struct_java

__all__ = [
    "generate_constants_java",
    "generate_decoder_java",
    "generate_decoder_registry_java",
    "generate_encoder_java",
    "generate_enum_java",
    "generate_log_method",
    "generate_messageid_java",
    "generate_protocol_callbacks_java",
    "generate_protocol_methods_java",
    "generate_protocol_template_java",
    "generate_struct_java",
]
