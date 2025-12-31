"""
C++ Code Generators for Serial8 Protocol
Generates C++ protocol files with 8-bit binary encoding.
"""

from protocol_codegen.generators.common.cpp import generate_protocol_callbacks_hpp
from .constants_generator import generate_constants_hpp
from .decoder_generator import generate_decoder_hpp
from .decoder_registry_generator import generate_decoder_registry_hpp
from .encoder_generator import generate_encoder_hpp
from protocol_codegen.generators.common.cpp import generate_enum_hpp
from protocol_codegen.generators.common.cpp import generate_logger_hpp
from protocol_codegen.generators.common.cpp import generate_message_structure_hpp
from protocol_codegen.generators.common.cpp import generate_messageid_hpp
from protocol_codegen.generators.common.cpp import generate_protocol_methods_hpp
from .protocol_generator import generate_protocol_template_hpp
from .struct_generator import generate_struct_hpp

__all__ = [
    "generate_constants_hpp",
    "generate_decoder_hpp",
    "generate_decoder_registry_hpp",
    "generate_encoder_hpp",
    "generate_enum_hpp",
    "generate_logger_hpp",
    "generate_message_structure_hpp",
    "generate_messageid_hpp",
    "generate_protocol_callbacks_hpp",
    "generate_protocol_methods_hpp",
    "generate_protocol_template_hpp",
    "generate_struct_hpp",
]
