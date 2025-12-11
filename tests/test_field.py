"""
Tests for field module (PrimitiveField, CompositeField).

Validates field creation, validation, and type safety.
"""

from __future__ import annotations

import pytest

from protocol_codegen.core.field import (
    CompositeField,
    PrimitiveField,
    Type,
)


class TestPrimitiveField:
    """Tests for PrimitiveField class."""

    def test_create_scalar_field(self) -> None:
        """Scalar field should have no array size."""
        field = PrimitiveField("value", type_name=Type.FLOAT32)

        assert field.name == "value"
        assert field.type_name == Type.FLOAT32
        assert field.array is None
        assert field.dynamic is False
        assert field.is_primitive() is True
        assert field.is_composite() is False
        assert field.is_array() is False

    def test_create_array_field(self) -> None:
        """Array field should have array size set."""
        field = PrimitiveField("values", type_name=Type.UINT8, array=16)

        assert field.name == "values"
        assert field.array == 16
        assert field.dynamic is False
        assert field.is_array() is True

    def test_create_dynamic_array_field(self) -> None:
        """Dynamic array field requires array size."""
        field = PrimitiveField("items", type_name=Type.UINT16, array=32, dynamic=True)

        assert field.dynamic is True
        assert field.array == 32

    def test_dynamic_without_array_raises(self) -> None:
        """Dynamic flag without array size should raise ValueError."""
        with pytest.raises(ValueError, match="dynamic=True requires array size"):
            PrimitiveField("bad", type_name=Type.UINT8, dynamic=True)

    def test_zero_array_size_raises(self) -> None:
        """Array size must be positive."""
        with pytest.raises(ValueError, match="Array size must be positive"):
            PrimitiveField("bad", type_name=Type.UINT8, array=0)

    def test_negative_array_size_raises(self) -> None:
        """Negative array size should raise ValueError."""
        with pytest.raises(ValueError, match="Array size must be positive"):
            PrimitiveField("bad", type_name=Type.UINT8, array=-1)

    def test_validate_depth_scalar(self) -> None:
        """Scalar field depth validation should pass."""
        field = PrimitiveField("value", type_name=Type.FLOAT32)
        field.validate_depth(max_depth=3, current_depth=0)  # Should not raise

    def test_validate_depth_exceeds_max(self) -> None:
        """Field at excessive depth should raise."""
        field = PrimitiveField("value", type_name=Type.FLOAT32)
        with pytest.raises(ValueError, match="exceeds maximum nesting depth"):
            field.validate_depth(max_depth=2, current_depth=3)

    def test_str_representation_scalar(self) -> None:
        """String representation of scalar field."""
        field = PrimitiveField("value", type_name=Type.FLOAT32)
        assert str(field) == "value: float32"

    def test_str_representation_array(self) -> None:
        """String representation of array field."""
        field = PrimitiveField("values", type_name=Type.UINT8, array=8)
        assert str(field) == "values: uint8[8]"


class TestCompositeField:
    """Tests for CompositeField class."""

    def test_create_composite_field(self) -> None:
        """Composite field should contain nested fields."""
        field = CompositeField(
            "reading",
            fields=[
                PrimitiveField("id", type_name=Type.UINT8),
                PrimitiveField("value", type_name=Type.FLOAT32),
            ],
        )

        assert field.name == "reading"
        assert len(field.fields) == 2
        assert field.array is None
        assert field.is_primitive() is False
        assert field.is_composite() is True
        assert field.is_array() is False

    def test_create_composite_array(self) -> None:
        """Composite array field should have array size."""
        field = CompositeField(
            "readings",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
            array=8,
        )

        assert field.array == 8
        assert field.is_array() is True

    def test_empty_fields_raises(self) -> None:
        """Composite field with no fields should raise ValueError."""
        with pytest.raises(ValueError, match="must have at least one field"):
            CompositeField("empty", fields=[])

    def test_zero_array_size_raises(self) -> None:
        """Array size must be positive."""
        with pytest.raises(ValueError, match="Array size must be positive"):
            CompositeField(
                "bad",
                fields=[PrimitiveField("id", type_name=Type.UINT8)],
                array=0,
            )

    def test_validate_depth_nested(self) -> None:
        """Nested composite fields should validate depth recursively."""
        inner = CompositeField(
            "inner",
            fields=[PrimitiveField("value", type_name=Type.UINT8)],
        )
        outer = CompositeField("outer", fields=[inner])

        outer.validate_depth(max_depth=3, current_depth=0)  # Should pass

    def test_validate_depth_exceeds_max_nested(self) -> None:
        """Deeply nested composite should raise at depth limit."""
        # Create 4-level deep nesting
        level3 = CompositeField(
            "level3",
            fields=[PrimitiveField("value", type_name=Type.UINT8)],
        )
        level2 = CompositeField("level2", fields=[level3])
        level1 = CompositeField("level1", fields=[level2])
        level0 = CompositeField("level0", fields=[level1])

        with pytest.raises(ValueError, match="exceeds maximum nesting depth"):
            level0.validate_depth(max_depth=2, current_depth=0)

    def test_str_representation(self) -> None:
        """String representation of composite field."""
        field = CompositeField(
            "reading",
            fields=[
                PrimitiveField("id", type_name=Type.UINT8),
                PrimitiveField("value", type_name=Type.FLOAT32),
            ],
        )
        assert str(field) == "reading: struct(2 fields)"

    def test_str_representation_array(self) -> None:
        """String representation of composite array field."""
        field = CompositeField(
            "readings",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
            array=8,
        )
        assert str(field) == "readings: struct(1 fields)[8]"


class TestTypeEnum:
    """Tests for dynamic Type enum."""

    def test_type_enum_has_builtin_types(self) -> None:
        """Type enum should have all builtin types after population."""
        expected_types = [
            "UINT8",
            "UINT16",
            "UINT32",
            "INT8",
            "INT16",
            "INT32",
            "FLOAT32",
            "STRING",
            "BOOL",
        ]
        for type_name in expected_types:
            assert hasattr(Type, type_name), f"Type.{type_name} should exist"

    def test_type_enum_value_matches_name(self) -> None:
        """Type enum value should be lowercase type name."""
        assert Type.UINT8.value == "uint8"
        assert Type.FLOAT32.value == "float32"
        assert Type.STRING.value == "string"

    def test_type_enum_is_string(self) -> None:
        """Type enum should inherit from str."""
        assert isinstance(Type.UINT8, str)
        assert Type.UINT8 == "uint8"
