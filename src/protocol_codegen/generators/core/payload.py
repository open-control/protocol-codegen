"""
Payload size calculator with strategy pattern.

Calculates MAX_PAYLOAD_SIZE and MIN_PAYLOAD_SIZE for message structs
using the appropriate encoding strategy for the protocol.

All arrays are treated uniformly with a count byte prefix (Binary style).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.core.field import CompositeField, EnumField, PrimitiveField

if TYPE_CHECKING:
    from collections.abc import Sequence

    from protocol_codegen.core.field import FieldBase
    from protocol_codegen.core.loader import TypeRegistry

    from .encoding.strategy import EncodingStrategy


class PayloadCalculator:
    """Calculate payload sizes using protocol-specific encoding strategy."""

    def __init__(self, strategy: EncodingStrategy, type_registry: TypeRegistry):
        self.strategy = strategy
        self.type_registry = type_registry

    def calculate_max_payload_size(
        self,
        fields: Sequence[FieldBase],
        string_max_length: int,
        name_prefix_size: int = 0,
    ) -> int:
        """
        Calculate maximum payload size in bytes.

        Args:
            fields: List of Field objects
            string_max_length: Max string length from config
            name_prefix_size: Size of MESSAGE_NAME prefix (0 if disabled)

        Returns:
            Maximum size in bytes
        """
        total_size = name_prefix_size

        for field in fields:
            total_size += self._get_field_max_size(field, string_max_length)

        return total_size

    def calculate_min_payload_size(
        self,
        fields: Sequence[FieldBase],
        string_max_length: int,
        name_prefix_size: int = 0,
    ) -> int:
        """
        Calculate minimum payload size in bytes (with empty strings/arrays).

        Args:
            fields: List of Field objects
            string_max_length: Max string length (unused, for signature compat)
            name_prefix_size: Size of MESSAGE_NAME prefix (0 if disabled)

        Returns:
            Minimum size in bytes
        """
        total_size = name_prefix_size

        for field in fields:
            total_size += self._get_field_min_size(field)

        return total_size

    def _get_field_max_size(self, field: FieldBase, string_max_length: int) -> int:
        """Calculate max size for a single field."""
        if isinstance(field, EnumField):
            return self._get_enum_max_size(field)
        elif isinstance(field, PrimitiveField):
            return self._get_primitive_max_size(field, string_max_length)
        elif isinstance(field, CompositeField):
            return self._get_composite_max_size(field, string_max_length)
        return 0

    def _get_field_min_size(self, field: FieldBase) -> int:
        """Calculate min size for a single field."""
        if isinstance(field, EnumField):
            return self._get_enum_min_size(field)
        elif isinstance(field, PrimitiveField):
            return self._get_primitive_min_size(field)
        elif isinstance(field, CompositeField):
            return self._get_composite_min_size(field)
        return 0

    def _get_enum_max_size(self, field: EnumField) -> int:
        """Enum field max size - 1 byte per value + optional count byte."""
        array_size = field.array if field.array else 1
        size = 1 * array_size  # 1 byte per enum value
        if field.array:
            size += 1  # Array count byte
        return size

    def _get_enum_min_size(self, field: EnumField) -> int:
        """Enum field min size."""
        if field.array:
            return 1  # Array count byte only (min = 0 elements)
        return 1  # 1 byte for enum value

    def _get_primitive_max_size(self, field: PrimitiveField, string_max_length: int) -> int:
        """Calculate max size for primitive field."""
        type_name = field.type_name.value
        array_size = field.array if field.array else 1

        if not self.type_registry.is_atomic(type_name):
            return 10 * array_size  # Conservative estimate

        atomic = self.type_registry.get(type_name)

        if atomic.is_builtin:
            if atomic.size_bytes == "variable":
                # String: length prefix + max chars
                base_size = self.strategy.get_string_max_encoded_size(string_max_length)
            else:
                assert isinstance(atomic.size_bytes, int)
                base_size = self.strategy.get_encoded_size(type_name, atomic.size_bytes)
        else:
            base_size = 10  # Conservative

        total = base_size * array_size
        if field.array:
            total += 1  # Array count byte (all arrays have count byte)

        return total

    def _get_primitive_min_size(self, field: PrimitiveField) -> int:
        """Calculate min size for primitive field."""
        type_name = field.type_name.value

        if not self.type_registry.is_atomic(type_name):
            return 10

        atomic = self.type_registry.get(type_name)

        if atomic.is_builtin:
            if atomic.size_bytes == "variable":
                # String: length prefix only (empty string)
                base_size = self.strategy.get_string_min_encoded_size()
            else:
                assert isinstance(atomic.size_bytes, int)
                base_size = self.strategy.get_encoded_size(type_name, atomic.size_bytes)
        else:
            base_size = 10

        if field.array:
            return 1  # Count byte only (min = 0 elements)
        return base_size

    def _get_composite_max_size(self, field: CompositeField, string_max_length: int) -> int:
        """Calculate max size for composite field."""
        nested_size = self.calculate_max_payload_size(field.fields, string_max_length)

        if field.array:
            return 1 + (nested_size * field.array)  # Count + items
        return nested_size

    def _get_composite_min_size(self, field: CompositeField) -> int:
        """Calculate min size for composite field."""
        if field.array:
            return 1  # Count byte only (min = 0 elements)
        return self.calculate_min_payload_size(field.fields, 0)
