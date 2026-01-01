"""
Common Java Generators.

Shared generators for Java code generation across protocols (SysEx, Serial8).

Note: Low-level struct_utils are intentionally not exposed here.
They are internal implementation details used by generate_struct_java.
"""

from protocol_codegen.generators.common.java.callbacks_generator import (
    generate_protocol_callbacks_java,
)
from protocol_codegen.generators.common.java.constants_generator import (
    generate_constants_java,
)
from protocol_codegen.generators.common.java.decoder_registry_generator import (
    generate_decoder_registry_java,
)
from protocol_codegen.generators.common.java.enum_generator import (
    generate_enum_java,
)
from protocol_codegen.generators.common.java.messageid_generator import (
    generate_messageid_java,
)
from protocol_codegen.generators.common.java.method_generator import (
    generate_protocol_methods_java,
)
from protocol_codegen.generators.common.java.struct_generator import (
    generate_struct_java,
)

__all__ = [
    # Callbacks
    "generate_protocol_callbacks_java",
    # Constants
    "generate_constants_java",
    # Decoder Registry
    "generate_decoder_registry_java",
    # Enum
    "generate_enum_java",
    # MessageID
    "generate_messageid_java",
    # Methods
    "generate_protocol_methods_java",
    # Struct Generator
    "generate_struct_java",
]
