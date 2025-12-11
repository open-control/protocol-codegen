"""
Tests for validator module (ProtocolValidator).

Validates message validation logic including type checking and error collection.
"""

from __future__ import annotations

from protocol_codegen.core.field import CompositeField, PrimitiveField, Type
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message
from protocol_codegen.core.validator import ProtocolValidator


def _create_message(name: str, fields: list[PrimitiveField | CompositeField]) -> Message:
    """Helper to create a message with given name and fields."""
    msg = Message(description=f"Test message {name}", fields=fields)
    msg.name = name
    return msg


class TestProtocolValidator:
    """Tests for ProtocolValidator class."""

    def test_validate_empty_messages_fails(self, type_registry: TypeRegistry) -> None:
        """Empty message list should produce an error."""
        validator = ProtocolValidator(type_registry)
        errors = validator.validate_messages([])

        assert len(errors) == 1
        assert "No messages defined" in errors[0]

    def test_validate_valid_message(self, type_registry: TypeRegistry) -> None:
        """Valid message should pass validation."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "SENSOR_READING",
                [
                    PrimitiveField("sensorId", type_name=Type.UINT8),
                    PrimitiveField("value", type_name=Type.FLOAT32),
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0
        assert validator.has_errors() is False

    def test_validate_all_builtin_types(self, type_registry: TypeRegistry) -> None:
        """All builtin types should pass validation."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "ALL_TYPES",
                [
                    PrimitiveField("f_bool", type_name=Type.BOOL),
                    PrimitiveField("f_uint8", type_name=Type.UINT8),
                    PrimitiveField("f_uint16", type_name=Type.UINT16),
                    PrimitiveField("f_uint32", type_name=Type.UINT32),
                    PrimitiveField("f_int8", type_name=Type.INT8),
                    PrimitiveField("f_int16", type_name=Type.INT16),
                    PrimitiveField("f_int32", type_name=Type.INT32),
                    PrimitiveField("f_float32", type_name=Type.FLOAT32),
                    PrimitiveField("f_string", type_name=Type.STRING),
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0

    def test_validate_duplicate_message_names(self, type_registry: TypeRegistry) -> None:
        """Duplicate message names should produce an error."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message("DUPLICATE", [PrimitiveField("id", type_name=Type.UINT8)]),
            _create_message("DUPLICATE", [PrimitiveField("value", type_name=Type.FLOAT32)]),
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) >= 1
        assert any("Duplicate message names" in e for e in errors)

    def test_validate_duplicate_field_names(self, type_registry: TypeRegistry) -> None:
        """Duplicate field names within a message should produce an error."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "BAD_MESSAGE",
                [
                    PrimitiveField("value", type_name=Type.UINT8),
                    PrimitiveField("value", type_name=Type.FLOAT32),  # Duplicate!
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) >= 1
        assert any("duplicate field names" in e for e in errors)

    def test_validate_empty_message_name(self, type_registry: TypeRegistry) -> None:
        """Empty message name should produce an error."""
        validator = ProtocolValidator(type_registry)
        msg = Message(
            description="Empty name",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )
        msg.name = ""
        errors = validator.validate_messages([msg])

        assert len(errors) >= 1
        assert any("empty name" in e for e in errors)

    def test_validate_composite_field(self, type_registry: TypeRegistry) -> None:
        """Composite fields should be validated recursively."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "WITH_COMPOSITE",
                [
                    CompositeField(
                        "reading",
                        fields=[
                            PrimitiveField("id", type_name=Type.UINT8),
                            PrimitiveField("value", type_name=Type.FLOAT32),
                        ],
                    )
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0

    def test_validate_composite_duplicate_nested_fields(self, type_registry: TypeRegistry) -> None:
        """Duplicate field names in composite should produce an error."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "BAD_COMPOSITE",
                [
                    CompositeField(
                        "reading",
                        fields=[
                            PrimitiveField("id", type_name=Type.UINT8),
                            PrimitiveField("id", type_name=Type.UINT16),  # Duplicate!
                        ],
                    )
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) >= 1
        assert any("duplicate nested field names" in e for e in errors)

    def test_validate_deeply_nested_composite(self, type_registry: TypeRegistry) -> None:
        """Deeply nested composites exceeding max depth should produce an error."""
        validator = ProtocolValidator(type_registry)

        # Create 5-level deep nesting (exceeds default max_depth=3)
        level4 = CompositeField("level4", fields=[PrimitiveField("value", type_name=Type.UINT8)])
        level3 = CompositeField("level3", fields=[level4])
        level2 = CompositeField("level2", fields=[level3])
        level1 = CompositeField("level1", fields=[level2])

        messages = [_create_message("DEEP_NESTED", [level1])]
        errors = validator.validate_messages(messages)

        assert len(errors) >= 1
        assert any("nesting depth" in e for e in errors)

    def test_error_collection_multiple_errors(self, type_registry: TypeRegistry) -> None:
        """Validator should collect ALL errors, not fail on first."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "BAD1",
                [
                    PrimitiveField("dup", type_name=Type.UINT8),
                    PrimitiveField("dup", type_name=Type.UINT8),  # Error 1
                ],
            ),
            _create_message(
                "BAD2",
                [
                    PrimitiveField("dup", type_name=Type.UINT8),
                    PrimitiveField("dup", type_name=Type.UINT8),  # Error 2
                ],
            ),
        ]
        errors = validator.validate_messages(messages)

        # Should have errors from BOTH messages
        assert len(errors) >= 2

    def test_get_errors_returns_copy(self, type_registry: TypeRegistry) -> None:
        """get_errors should return a copy, not the internal list."""
        validator = ProtocolValidator(type_registry)
        validator.validate_messages([])  # Will produce "No messages" error

        errors1 = validator.get_errors()
        errors2 = validator.get_errors()

        assert errors1 == errors2
        assert errors1 is not errors2  # Different list instances

    def test_clear_errors(self, type_registry: TypeRegistry) -> None:
        """clear_errors should reset error state."""
        validator = ProtocolValidator(type_registry)
        validator.validate_messages([])  # Will produce error
        assert validator.has_errors() is True

        validator.clear_errors()
        assert validator.has_errors() is False
        assert len(validator.get_errors()) == 0

    def test_validate_array_field(self, type_registry: TypeRegistry) -> None:
        """Array fields should be validated correctly."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "WITH_ARRAY",
                [PrimitiveField("values", type_name=Type.UINT8, array=8)],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0

    def test_validate_composite_array_field(self, type_registry: TypeRegistry) -> None:
        """Composite array fields should be validated correctly."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(
                "WITH_COMPOSITE_ARRAY",
                [
                    CompositeField(
                        "readings",
                        fields=[
                            PrimitiveField("id", type_name=Type.UINT8),
                            PrimitiveField("value", type_name=Type.FLOAT32),
                        ],
                        array=8,
                    )
                ],
            )
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0


class TestValidatorEdgeCases:
    """Edge case tests for validator."""

    def test_message_with_no_fields(self, type_registry: TypeRegistry) -> None:
        """Message with no fields should be valid (request messages)."""
        validator = ProtocolValidator(type_registry)
        messages = [_create_message("REQUEST_STATUS", [])]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0

    def test_many_messages_valid(self, type_registry: TypeRegistry) -> None:
        """Should handle many valid messages without issue."""
        validator = ProtocolValidator(type_registry)
        messages = [
            _create_message(f"MSG_{i}", [PrimitiveField("id", type_name=Type.UINT8)])
            for i in range(100)
        ]
        errors = validator.validate_messages(messages)

        assert len(errors) == 0
