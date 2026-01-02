"""
Core utilities for code generators.

This module contains shared utilities that are language and protocol agnostic:
- config: Protocol configuration structures
- naming: Naming conversion utilities
- payload: Payload size calculation
- encoding_ops: Encoding operation dataclasses
- type_encoders: Type-specific encoding logic
- type_decoders: Type-specific decoding logic
"""

from protocol_codegen.generators.core import type_decoders, type_encoders
from protocol_codegen.generators.core.config import (
    LimitsConfig,
    ProtocolConfig,
    StructureConfig,
    SysExFramingConfig,
)
from protocol_codegen.generators.core.encoding_ops import (
    ByteReadOp,
    ByteWriteOp,
    DecoderMethodSpec,
    MethodSpec,
)
from protocol_codegen.generators.core.naming import (
    message_name_to_callback_name,
    message_name_to_method_name,
    should_exclude_field,
    to_camel_case,
    to_pascal_case,
)
from protocol_codegen.generators.core.payload import PayloadCalculator

__all__ = [
    # Subpackages
    "type_decoders",
    "type_encoders",
    # Config TypedDicts
    "LimitsConfig",
    "ProtocolConfig",
    "StructureConfig",
    "SysExFramingConfig",
    # Encoding operations
    "ByteReadOp",
    "ByteWriteOp",
    "DecoderMethodSpec",
    "MethodSpec",
    # Naming utilities
    "message_name_to_callback_name",
    "message_name_to_method_name",
    "should_exclude_field",
    "to_camel_case",
    "to_pascal_case",
    # Payload calculator
    "PayloadCalculator",
]
