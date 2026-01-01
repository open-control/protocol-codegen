"""
Common C++ Generators.

Shared generators for C++ code generation across protocols (SysEx, Serial8).

Note: Low-level struct_utils are intentionally not exposed here.
They are internal implementation details used by generate_struct_hpp.
"""

from protocol_codegen.generators.common.cpp.callbacks_generator import (
    generate_protocol_callbacks_hpp,
)
from protocol_codegen.generators.common.cpp.constants_generator import (
    generate_constants_hpp,
)
from protocol_codegen.generators.common.cpp.decoder_registry_generator import (
    generate_decoder_registry_hpp,
)
from protocol_codegen.generators.common.cpp.enum_generator import (
    generate_enum_hpp,
)
from protocol_codegen.generators.common.cpp.message_structure_generator import (
    generate_message_structure_hpp,
)
from protocol_codegen.generators.common.cpp.messageid_generator import (
    generate_messageid_hpp,
)
from protocol_codegen.generators.common.cpp.method_generator import (
    generate_protocol_methods_hpp,
)
from protocol_codegen.generators.common.cpp.struct_generator import (
    generate_struct_hpp,
)

__all__ = [
    # Callbacks
    "generate_protocol_callbacks_hpp",
    # Constants
    "generate_constants_hpp",
    # Decoder Registry
    "generate_decoder_registry_hpp",
    # Enum
    "generate_enum_hpp",
    # Message Structure
    "generate_message_structure_hpp",
    # MessageID
    "generate_messageid_hpp",
    # Methods
    "generate_protocol_methods_hpp",
    # Struct Generator
    "generate_struct_hpp",
]
