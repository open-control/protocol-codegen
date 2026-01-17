"""
Common utilities for protocol generators.

Shared functions used by both Binary and SysEx orchestrators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.field import CompositeField, EnumField

if TYPE_CHECKING:
    from protocol_codegen.core.message import Message


def collect_enum_defs(messages: list[Message]) -> list[EnumDef]:
    """
    Collect all unique EnumDef instances from message fields.

    Traverses all messages and their fields (including nested composites)
    to find EnumField instances and extract their EnumDef references.

    Args:
        messages: List of Message instances to scan

    Returns:
        List of unique EnumDef instances (deduplicated by name)
    """
    seen_names: set[str] = set()
    enum_defs: list[EnumDef] = []

    def collect_from_fields(fields: list) -> None:
        """Recursively collect EnumDefs from a list of fields."""
        for field in fields:
            if isinstance(field, EnumField):
                if field.enum_def.name not in seen_names:
                    seen_names.add(field.enum_def.name)
                    enum_defs.append(field.enum_def)
            elif isinstance(field, CompositeField):
                # Recurse into composite fields
                collect_from_fields(list(field.fields))

    for message in messages:
        collect_from_fields(list(message.fields))

    return enum_defs
