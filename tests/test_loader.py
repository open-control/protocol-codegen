"""
Tests for loader module (TypeRegistry, AtomicType).

Validates type loading, registration, and validation.
"""

from __future__ import annotations

import pytest

from protocol_codegen.core.loader import AtomicType, TypeRegistry


class TestAtomicType:
    """Tests for AtomicType dataclass."""

    def test_create_builtin_type(self) -> None:
        """Builtin type should have no fields but have size info."""
        atomic = AtomicType(
            name="uint8",
            description="8-bit unsigned integer",
            fields=[],
            is_builtin=True,
            size_bytes=1,
            cpp_type="uint8_t",
            java_type="int",
        )

        assert atomic.name == "uint8"
        assert atomic.is_builtin is True
        assert atomic.size_bytes == 1
        assert atomic.cpp_type == "uint8_t"
        assert len(atomic.fields) == 0

    def test_create_custom_type(self) -> None:
        """Custom type should have fields but no size info."""
        atomic = AtomicType(
            name="SensorReading",
            description="Sensor reading struct",
            fields=[("sensorId", "uint8"), ("value", "float32")],
            is_builtin=False,
        )

        assert atomic.name == "SensorReading"
        assert atomic.is_builtin is False
        assert len(atomic.fields) == 2
        assert atomic.size_bytes is None

    def test_str_representation_builtin(self) -> None:
        """String representation of builtin type."""
        atomic = AtomicType(
            name="uint8",
            description="8-bit unsigned integer",
            fields=[],
            is_builtin=True,
        )
        assert "builtin" in str(atomic)
        assert "uint8" in str(atomic)

    def test_str_representation_custom(self) -> None:
        """String representation of custom type."""
        atomic = AtomicType(
            name="SensorReading",
            description="Sensor reading struct",
            fields=[("sensorId", "uint8")],
            is_builtin=False,
        )
        assert "custom" in str(atomic)
        assert "SensorReading" in str(atomic)


class TestTypeRegistry:
    """Tests for TypeRegistry class."""

    def test_empty_registry(self) -> None:
        """New registry should be empty."""
        registry = TypeRegistry()

        assert len(registry.types) == 0
        assert registry.has_errors() is False

    def test_load_builtins(self, type_registry: TypeRegistry) -> None:
        """Registry should have all builtin types after loading."""
        expected_types = [
            "uint8",
            "uint16",
            "uint32",
            "int8",
            "int16",
            "int32",
            "float32",
            "string",
            "bool",
        ]

        for type_name in expected_types:
            assert type_registry.is_atomic(type_name), f"{type_name} should be registered"

    def test_builtin_properties(self, type_registry: TypeRegistry) -> None:
        """Builtin types should have correct properties."""
        uint8 = type_registry.get("uint8")

        assert uint8.is_builtin is True
        assert uint8.size_bytes == 1
        assert uint8.cpp_type == "uint8_t"
        assert uint8.java_type == "int"

    def test_float32_properties(self, type_registry: TypeRegistry) -> None:
        """Float32 type should have correct mapping."""
        float32 = type_registry.get("float32")

        assert float32.is_builtin is True
        assert float32.size_bytes == 4
        assert float32.cpp_type == "float"
        assert float32.java_type == "float"

    def test_string_properties(self, type_registry: TypeRegistry) -> None:
        """String type should have variable size."""
        string = type_registry.get("string")

        assert string.is_builtin is True
        assert string.size_bytes == "variable"
        assert string.cpp_type == "std::string"
        assert string.java_type == "String"

    def test_add_custom_type(self, type_registry: TypeRegistry) -> None:
        """Custom types should be addable to registry."""
        type_registry.add_custom_type(
            name="SensorReading",
            description="Sensor reading struct",
            fields=[("sensorId", "uint8"), ("value", "float32")],
        )

        assert type_registry.is_atomic("SensorReading")
        custom = type_registry.get("SensorReading")
        assert custom.is_builtin is False
        assert len(custom.fields) == 2

    def test_is_atomic_returns_false_for_unknown(self, type_registry: TypeRegistry) -> None:
        """is_atomic should return False for unregistered types."""
        assert type_registry.is_atomic("NonExistentType") is False

    def test_get_raises_for_unknown(self, type_registry: TypeRegistry) -> None:
        """get should raise KeyError for unregistered types."""
        with pytest.raises(KeyError):
            type_registry.get("NonExistentType")

    def test_validate_references_valid(self, type_registry: TypeRegistry) -> None:
        """Validation should pass for valid type references."""
        type_registry.add_custom_type(
            name="SensorReading",
            description="Sensor reading",
            fields=[("sensorId", "uint8"), ("value", "float32")],
        )
        type_registry.validate_references()

        assert type_registry.has_errors() is False

    def test_validate_references_with_array(self, type_registry: TypeRegistry) -> None:
        """Validation should handle array notation."""
        type_registry.add_custom_type(
            name="SensorBatch",
            description="Batch of readings",
            fields=[("values", "uint8[8]"), ("count", "uint8")],
        )
        type_registry.validate_references()

        assert type_registry.has_errors() is False

    def test_validate_references_invalid(self, type_registry: TypeRegistry) -> None:
        """Validation should catch invalid type references."""
        type_registry.add_custom_type(
            name="BadType",
            description="Bad type",
            fields=[("value", "nonexistent_type")],
        )
        type_registry.validate_references()

        assert type_registry.has_errors() is True
        errors = type_registry.get_errors()
        assert any("nonexistent_type" in e for e in errors)

    def test_clear_errors(self, type_registry: TypeRegistry) -> None:
        """clear_errors should reset error state."""
        type_registry.add_custom_type(
            name="BadType",
            description="Bad type",
            fields=[("value", "nonexistent")],
        )
        type_registry.validate_references()
        assert type_registry.has_errors() is True

        type_registry.clear_errors()
        assert type_registry.has_errors() is False


class TestTypeRegistryBuiltinCoverage:
    """Tests to ensure all builtin types are correctly defined."""

    def test_all_integer_types_present(self, type_registry: TypeRegistry) -> None:
        """All integer types should be present."""
        integer_types = ["uint8", "uint16", "uint32", "int8", "int16", "int32"]
        for type_name in integer_types:
            assert type_registry.is_atomic(type_name)
            atomic = type_registry.get(type_name)
            assert atomic.cpp_type is not None
            assert atomic.java_type is not None
            assert isinstance(atomic.size_bytes, int)

    def test_bool_type_present(self, type_registry: TypeRegistry) -> None:
        """Bool type should be present with correct mappings."""
        assert type_registry.is_atomic("bool")
        bool_type = type_registry.get("bool")
        assert bool_type.cpp_type == "bool"
        assert bool_type.java_type == "boolean"
        assert bool_type.size_bytes == 1

    def test_float_type_present(self, type_registry: TypeRegistry) -> None:
        """Float32 type should be present."""
        assert type_registry.is_atomic("float32")
        float_type = type_registry.get("float32")
        assert float_type.size_bytes == 4

    def test_no_float64_type(self, type_registry: TypeRegistry) -> None:
        """Float64 should not be present (MIDI limitation)."""
        assert type_registry.is_atomic("float64") is False
