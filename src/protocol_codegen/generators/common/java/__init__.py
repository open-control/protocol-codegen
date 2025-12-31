"""
Common Java Generators.

Shared generators for Java code generation across protocols (SysEx, Serial8).
"""

from protocol_codegen.generators.common.java.callbacks_generator import (
    generate_protocol_callbacks_java,
)
from protocol_codegen.generators.common.java.enum_generator import (
    generate_enum_java,
)
from protocol_codegen.generators.common.java.decoder_registry_generator import (
    generate_decoder_registry_java,
)
from protocol_codegen.generators.common.java.messageid_generator import (
    generate_messageid_java,
)
from protocol_codegen.generators.common.java.logger_generator import (
    generate_log_method,
)
from protocol_codegen.generators.common.java.method_generator import (
    generate_protocol_methods_java,
)

__all__ = [
    "generate_log_method",
    "generate_decoder_registry_java",
    "generate_enum_java",
    "generate_messageid_java",
    "generate_protocol_callbacks_java",
    "generate_protocol_methods_java",
]
