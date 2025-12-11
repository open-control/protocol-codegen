"""
Protocol CodeGen - Core module

Provides the core type system, message definitions, and validation.
"""

from protocol_codegen.core.allocator import allocate_message_ids
from protocol_codegen.core.field import (
    CompositeField,
    PrimitiveField,
    Type,
    populate_type_names,
)
from protocol_codegen.core.file_utils import GenerationStats, write_if_changed
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message, collect_messages
from protocol_codegen.core.types import BUILTIN_TYPES, BuiltinTypeDef
from protocol_codegen.core.validator import ProtocolValidator

__all__ = [
    "PrimitiveField",
    "CompositeField",
    "Type",
    "populate_type_names",
    "Message",
    "collect_messages",
    "BUILTIN_TYPES",
    "BuiltinTypeDef",
    "TypeRegistry",
    "ProtocolValidator",
    "allocate_message_ids",
    "GenerationStats",
    "write_if_changed",
]
