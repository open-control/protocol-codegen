"""
Tests for message module (Message dataclass).

Validates message creation and properties.
"""

from __future__ import annotations

from protocol_codegen.core.enums import Direction, Intent
from protocol_codegen.core.field import CompositeField, PrimitiveField, Type
from protocol_codegen.core.message import (
    Message,
    collect_messages,
    is_screaming_snake_case,
)


class TestMessage:
    """Tests for Message dataclass."""

    def test_create_message(self) -> None:
        """Basic message creation."""
        msg = Message(
            description="Test message",
            fields=[PrimitiveField("value", type_name=Type.FLOAT32)],
        )
        msg.name = "TEST_MESSAGE"

        assert msg.name == "TEST_MESSAGE"
        assert msg.description == "Test message"
        assert len(msg.fields) == 1
        assert msg.optimistic is False

    def test_create_message_with_optimistic(self) -> None:
        """Message with optimistic updates enabled."""
        msg = Message(
            description="Optimistic message",
            fields=[PrimitiveField("value", type_name=Type.FLOAT32)],
            optimistic=True,
        )

        assert msg.optimistic is True

    def test_create_empty_message(self) -> None:
        """Message with no fields (request message)."""
        msg = Message(
            description="Request message",
            fields=[],
        )
        msg.name = "REQUEST_STATUS"

        assert len(msg.fields) == 0

    def test_message_default_name(self) -> None:
        """Message should have empty default name."""
        msg = Message(
            description="Test",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )

        assert msg.name == ""

    def test_str_representation_with_name(self) -> None:
        """String representation with name set."""
        msg = Message(
            description="Test message",
            fields=[
                PrimitiveField("id", type_name=Type.UINT8),
                PrimitiveField("value", type_name=Type.FLOAT32),
            ],
        )
        msg.name = "SENSOR_READING"

        assert str(msg) == "Message(SENSOR_READING, 2 fields)"

    def test_str_representation_without_name(self) -> None:
        """String representation without name set."""
        msg = Message(
            description="Test message",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )

        assert str(msg) == "Message(UNNAMED, 1 fields)"

    def test_message_with_composite_field(self) -> None:
        """Message containing composite fields."""
        msg = Message(
            description="Complex message",
            fields=[
                PrimitiveField("count", type_name=Type.UINT8),
                CompositeField(
                    "readings",
                    fields=[
                        PrimitiveField("id", type_name=Type.UINT8),
                        PrimitiveField("value", type_name=Type.FLOAT32),
                    ],
                    array=8,
                ),
            ],
        )
        msg.name = "SENSOR_BATCH"

        assert len(msg.fields) == 2
        assert msg.fields[0].is_primitive()
        assert msg.fields[1].is_composite()

    def test_message_with_array_fields(self) -> None:
        """Message containing array fields."""
        msg = Message(
            description="Array message",
            fields=[
                PrimitiveField("ids", type_name=Type.UINT8, array=16),
                PrimitiveField("values", type_name=Type.FLOAT32, array=16),
            ],
        )
        msg.name = "BATCH_VALUES"

        assert msg.fields[0].is_array()
        assert msg.fields[1].is_array()

    def test_message_immutability_fields(self) -> None:
        """Message fields should be stored as provided (Sequence)."""
        fields = [
            PrimitiveField("id", type_name=Type.UINT8),
            PrimitiveField("value", type_name=Type.FLOAT32),
        ]
        msg = Message(description="Test", fields=fields)

        # Original list should work with message
        assert len(msg.fields) == 2


class TestMessageEdgeCases:
    """Edge case tests for Message."""

    def test_message_with_many_fields(self) -> None:
        """Message with many fields should work."""
        fields = [PrimitiveField(f"field_{i}", type_name=Type.UINT8) for i in range(50)]
        msg = Message(description="Many fields", fields=fields)
        msg.name = "MANY_FIELDS"

        assert len(msg.fields) == 50

    def test_message_field_access(self) -> None:
        """Fields should be accessible by index."""
        msg = Message(
            description="Test",
            fields=[
                PrimitiveField("first", type_name=Type.UINT8),
                PrimitiveField("second", type_name=Type.FLOAT32),
            ],
        )

        assert msg.fields[0].name == "first"
        assert msg.fields[1].name == "second"

    def test_message_description_can_be_empty(self) -> None:
        """Empty description should be allowed."""
        msg = Message(
            description="",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )

        assert msg.description == ""


class TestIsScreamingSnakeCase:
    """Tests for is_screaming_snake_case helper function."""

    def test_valid_screaming_snake_case(self) -> None:
        """Valid SCREAMING_SNAKE_CASE names should return True."""
        assert is_screaming_snake_case("SENSOR_READING") is True
        assert is_screaming_snake_case("TRANSPORT_PLAY") is True
        assert is_screaming_snake_case("MSG") is True
        assert is_screaming_snake_case("A") is True
        assert is_screaming_snake_case("MSG_1") is True
        assert is_screaming_snake_case("MSG123") is True

    def test_invalid_lowercase(self) -> None:
        """Lowercase names should return False."""
        assert is_screaming_snake_case("sensor_reading") is False
        assert is_screaming_snake_case("sensorReading") is False
        assert is_screaming_snake_case("Sensor_Reading") is False

    def test_invalid_mixed_case(self) -> None:
        """Mixed case names should return False."""
        assert is_screaming_snake_case("SENSOR_reading") is False
        assert is_screaming_snake_case("SENSORReading") is False

    def test_invalid_private_names(self) -> None:
        """Private names (underscore prefix) should return False."""
        assert is_screaming_snake_case("_PRIVATE") is False
        assert is_screaming_snake_case("__DUNDER__") is False

    def test_invalid_empty_string(self) -> None:
        """Empty string should return False."""
        assert is_screaming_snake_case("") is False

    def test_invalid_special_chars(self) -> None:
        """Names with special characters should return False."""
        assert is_screaming_snake_case("MSG-NAME") is False
        assert is_screaming_snake_case("MSG.NAME") is False


class TestCollectMessages:
    """Tests for collect_messages function."""

    def test_collect_from_empty_globals(self) -> None:
        """Empty globals should return empty list."""
        messages = collect_messages({})
        assert messages == []

    def test_collect_single_message(self) -> None:
        """Should collect single message and inject name."""
        msg = Message(
            description="Test",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )
        fake_globals = {"SENSOR_READING": msg}

        messages = collect_messages(fake_globals)

        assert len(messages) == 1
        assert messages[0].name == "SENSOR_READING"
        assert messages[0] is msg

    def test_collect_multiple_messages(self) -> None:
        """Should collect all messages and inject names."""
        msg1 = Message(description="First", fields=[])
        msg2 = Message(description="Second", fields=[])

        fake_globals = {
            "ZEBRA_MSG": msg1,
            "ALPHA_MSG": msg2,
        }

        messages = collect_messages(fake_globals)

        assert len(messages) == 2
        # Should be sorted alphabetically
        assert messages[0].name == "ALPHA_MSG"
        assert messages[1].name == "ZEBRA_MSG"

    def test_ignore_non_message_values(self) -> None:
        """Should ignore non-Message values even with valid names."""
        msg = Message(description="Real message", fields=[])

        fake_globals = {
            "REAL_MESSAGE": msg,
            "FAKE_MESSAGE": "not a message",
            "ANOTHER_FAKE": 42,
            "YET_ANOTHER": None,
        }

        messages = collect_messages(fake_globals)

        assert len(messages) == 1
        assert messages[0].name == "REAL_MESSAGE"

    def test_ignore_non_screaming_snake_case(self) -> None:
        """Should ignore messages with invalid naming convention."""
        msg1 = Message(description="Valid", fields=[])
        msg2 = Message(description="Invalid lowercase", fields=[])
        msg3 = Message(description="Invalid mixed", fields=[])

        fake_globals = {
            "VALID_MESSAGE": msg1,
            "invalid_message": msg2,
            "InvalidMessage": msg3,
        }

        messages = collect_messages(fake_globals)

        assert len(messages) == 1
        assert messages[0].name == "VALID_MESSAGE"

    def test_ignore_private_names(self) -> None:
        """Should ignore messages with private naming."""
        msg1 = Message(description="Public", fields=[])
        msg2 = Message(description="Private", fields=[])

        fake_globals = {
            "PUBLIC_MESSAGE": msg1,
            "_PRIVATE_MESSAGE": msg2,
        }

        messages = collect_messages(fake_globals)

        assert len(messages) == 1
        assert messages[0].name == "PUBLIC_MESSAGE"

    def test_deterministic_ordering(self) -> None:
        """Order should be deterministic regardless of dict iteration order."""
        msg_a = Message(description="A", fields=[])
        msg_b = Message(description="B", fields=[])
        msg_c = Message(description="C", fields=[])

        # Create globals in random order
        fake_globals = {
            "MSG_C": msg_c,
            "MSG_A": msg_a,
            "MSG_B": msg_b,
        }

        messages = collect_messages(fake_globals)

        assert [m.name for m in messages] == ["MSG_A", "MSG_B", "MSG_C"]

    def test_name_injection_modifies_original(self) -> None:
        """Name injection should modify the original message object."""
        msg = Message(description="Test", fields=[])
        assert msg.name == ""  # Default empty

        fake_globals = {"TEST_MESSAGE": msg}
        collect_messages(fake_globals)

        assert msg.name == "TEST_MESSAGE"  # Now set


class TestMessageDirection:
    """Tests for message direction and intent (Phase 0 of protocol migration)."""

    def test_legacy_message_has_no_direction(self) -> None:
        """Messages without direction are legacy."""
        msg = Message(description="Legacy message", fields=[])

        assert msg.is_legacy() is True
        assert msg.direction is None
        assert msg.intent is None

    def test_new_message_has_direction(self) -> None:
        """New messages have explicit direction."""
        msg = Message(
            description="New message",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
        )

        assert msg.is_legacy() is False
        assert msg.is_to_host() is True
        assert msg.is_to_controller() is False
        assert msg.is_command() is True

    def test_to_controller_direction(self) -> None:
        """Message with TO_CONTROLLER direction."""
        msg = Message(
            description="Controller-bound message",
            fields=[],
            direction=Direction.TO_CONTROLLER,
            intent=Intent.NOTIFY,
        )

        assert msg.is_to_host() is False
        assert msg.is_to_controller() is True
        assert msg.is_notify() is True

    def test_query_message(self) -> None:
        """Query message expects a response."""
        msg = Message(
            description="Query message",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.QUERY,
        )

        assert msg.is_query() is True
        assert msg.is_response() is False

    def test_response_links_to_query(self) -> None:
        """Response messages link to their query."""
        response = Message(
            description="Response",
            fields=[],
            direction=Direction.TO_CONTROLLER,
            intent=Intent.RESPONSE,
            response_to="DEVICE_LIST_QUERY",
        )

        assert response.is_response() is True
        assert response.response_to == "DEVICE_LIST_QUERY"


class TestMessageDeprecated:
    """Tests for deprecated messages."""

    def test_deprecated_default_is_false(self) -> None:
        """Messages are not deprecated by default."""
        msg = Message(description="Active message", fields=[])

        assert msg.deprecated is False

    def test_deprecated_message(self) -> None:
        """Deprecated messages should be filterable."""
        msg = Message(description="Old message", fields=[], deprecated=True)

        assert msg.deprecated is True

    def test_deprecated_with_direction(self) -> None:
        """Deprecated messages can have direction."""
        msg = Message(
            description="Deprecated but typed",
            fields=[],
            direction=Direction.TO_HOST,
            intent=Intent.COMMAND,
            deprecated=True,
        )

        assert msg.deprecated is True
        assert msg.is_to_host() is True
