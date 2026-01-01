"""
Common C++ Generators.

Shared generators for C++ code generation across protocols (SysEx, Serial8).
"""

from protocol_codegen.generators.common.cpp.callbacks_generator import (
    generate_protocol_callbacks_hpp,
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

__all__ = [
    "generate_enum_hpp",
    "generate_message_structure_hpp",
    "generate_messageid_hpp",
    "generate_protocol_callbacks_hpp",
    "generate_protocol_methods_hpp",
]
