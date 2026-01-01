"""
Common utilities for code generators.

Subpackages:
- encoding: Protocol encoding strategies (Serial8, SysEx)
- type_encoders: Type-specific encoding logic
- type_decoders: Type-specific decoding logic
- cpp: C++ generation utilities
- java: Java generation utilities
"""

# Submodules
from protocol_codegen.generators.common import cpp, encoding, java, type_decoders, type_encoders
from protocol_codegen.generators.common.config import (
    LimitsConfig,
    ProtocolConfig,
    StructureConfig,
    SysExFramingConfig,
)
from protocol_codegen.generators.common.naming import (
    message_name_to_callback_name,
    message_name_to_method_name,
    to_camel_case,
    to_pascal_case,
)

__all__ = [
    # Subpackages
    "cpp",
    "encoding",
    "java",
    "type_decoders",
    "type_encoders",
    # Config TypedDicts
    "LimitsConfig",
    "ProtocolConfig",
    "StructureConfig",
    "SysExFramingConfig",
    # Naming utilities
    "message_name_to_callback_name",
    "message_name_to_method_name",
    "to_camel_case",
    "to_pascal_case",
]
