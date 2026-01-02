"""
Java File Generators.

Individual generators for Java protocol files.
"""

from protocol_codegen.generators.languages.java.file_generators.callbacks import (
    generate_protocol_callbacks_java,
)
from protocol_codegen.generators.languages.java.file_generators.constants import (
    generate_constants_java,
)
from protocol_codegen.generators.languages.java.file_generators.decoder_registry import (
    generate_decoder_registry_java,
)
from protocol_codegen.generators.languages.java.file_generators.enum import (
    generate_enum_java,
)
from protocol_codegen.generators.languages.java.file_generators.message_structure import (
    generate_message_structure_java,
)
from protocol_codegen.generators.languages.java.file_generators.messageid import (
    generate_messageid_java,
)
from protocol_codegen.generators.languages.java.file_generators.method import (
    generate_protocol_methods_java,
)
from protocol_codegen.generators.languages.java.file_generators.struct import (
    generate_struct_java,
)

__all__ = [
    "generate_protocol_callbacks_java",
    "generate_constants_java",
    "generate_decoder_registry_java",
    "generate_enum_java",
    "generate_message_structure_java",
    "generate_messageid_java",
    "generate_protocol_methods_java",
    "generate_struct_java",
]
