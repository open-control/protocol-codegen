"""
Tests for allocator module (message ID allocation).

Validates deterministic ID allocation and boundary conditions.
"""

from __future__ import annotations

import pytest

from protocol_codegen.core.allocator import allocate_message_ids
from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message


def _create_message(name: str) -> Message:
    """Helper to create a minimal message with given name."""
    msg = Message(
        description=f"Test message {name}",
        fields=[PrimitiveField("id", type_name=Type.UINT8)],
    )
    msg.name = name
    return msg


class TestAllocateMessageIds:
    """Tests for allocate_message_ids function."""

    def test_empty_messages(self) -> None:
        """Empty message list should return empty allocations."""
        allocations = allocate_message_ids([])
        assert allocations == {}

    def test_single_message(self) -> None:
        """Single message should get ID 0."""
        messages = [_create_message("TEST_MESSAGE")]
        allocations = allocate_message_ids(messages)

        assert allocations == {"TEST_MESSAGE": 0}

    def test_multiple_messages_alphabetical_order(self) -> None:
        """Messages should be allocated IDs in alphabetical order."""
        messages = [
            _create_message("ZEBRA_MSG"),
            _create_message("ALPHA_MSG"),
            _create_message("MIDDLE_MSG"),
        ]
        allocations = allocate_message_ids(messages)

        # Alphabetical: ALPHA < MIDDLE < ZEBRA
        assert allocations["ALPHA_MSG"] == 0
        assert allocations["MIDDLE_MSG"] == 1
        assert allocations["ZEBRA_MSG"] == 2

    def test_deterministic_allocation(self) -> None:
        """Same messages should always get same IDs regardless of input order."""
        messages_order1 = [
            _create_message("MSG_C"),
            _create_message("MSG_A"),
            _create_message("MSG_B"),
        ]
        messages_order2 = [
            _create_message("MSG_B"),
            _create_message("MSG_C"),
            _create_message("MSG_A"),
        ]

        alloc1 = allocate_message_ids(messages_order1)
        alloc2 = allocate_message_ids(messages_order2)

        assert alloc1 == alloc2
        assert alloc1["MSG_A"] == 0
        assert alloc1["MSG_B"] == 1
        assert alloc1["MSG_C"] == 2

    def test_custom_start_id(self) -> None:
        """Allocation should start from custom start_id."""
        messages = [
            _create_message("MSG_A"),
            _create_message("MSG_B"),
        ]
        allocations = allocate_message_ids(messages, start_id=0x10)

        assert allocations["MSG_A"] == 0x10
        assert allocations["MSG_B"] == 0x11

    def test_sequential_ids(self) -> None:
        """IDs should be strictly sequential with no gaps."""
        messages = [_create_message(f"MSG_{i:02d}") for i in range(10)]
        allocations = allocate_message_ids(messages)

        ids = sorted(allocations.values())
        assert ids == list(range(10))

    def test_max_256_messages(self) -> None:
        """Should handle up to 256 messages."""
        messages = [_create_message(f"MSG_{i:03d}") for i in range(256)]
        allocations = allocate_message_ids(messages)

        assert len(allocations) == 256
        assert max(allocations.values()) == 255

    def test_exceeds_256_messages_raises(self) -> None:
        """More than 256 messages should raise ValueError."""
        messages = [_create_message(f"MSG_{i:03d}") for i in range(257)]

        with pytest.raises(ValueError, match="Too many messages: 257"):
            allocate_message_ids(messages)

    def test_stability_after_adding_message(self) -> None:
        """
        Adding a new message should not change existing IDs.

        This is critical for protocol compatibility - existing message IDs
        must remain stable when new messages are added.
        """
        original_messages = [
            _create_message("MSG_BETA"),
            _create_message("MSG_GAMMA"),
        ]
        original_alloc = allocate_message_ids(original_messages)

        # Add a message that sorts AFTER existing ones
        extended_messages = original_messages + [_create_message("MSG_ZETA")]
        extended_alloc = allocate_message_ids(extended_messages)

        # Original IDs should be unchanged
        assert extended_alloc["MSG_BETA"] == original_alloc["MSG_BETA"]
        assert extended_alloc["MSG_GAMMA"] == original_alloc["MSG_GAMMA"]
        # New message gets the next ID
        assert extended_alloc["MSG_ZETA"] == 2

    def test_insertion_affects_later_ids(self) -> None:
        """
        Adding a message that sorts BEFORE existing ones shifts their IDs.

        This is expected behavior - alphabetical sorting means early names
        get early IDs. Document this for protocol versioning.
        """
        original_messages = [
            _create_message("MSG_BETA"),
            _create_message("MSG_GAMMA"),
        ]
        original_alloc = allocate_message_ids(original_messages)

        # Add a message that sorts BEFORE existing ones
        extended_messages = original_messages + [_create_message("MSG_ALPHA")]
        extended_alloc = allocate_message_ids(extended_messages)

        # ALPHA gets ID 0, pushing BETA and GAMMA up
        assert extended_alloc["MSG_ALPHA"] == 0
        assert extended_alloc["MSG_BETA"] == original_alloc["MSG_BETA"] + 1
        assert extended_alloc["MSG_GAMMA"] == original_alloc["MSG_GAMMA"] + 1


class TestAllocationEdgeCases:
    """Edge case tests for ID allocation."""

    def test_similar_names(self) -> None:
        """Similar names should sort correctly."""
        messages = [
            _create_message("MSG_10"),
            _create_message("MSG_1"),
            _create_message("MSG_2"),
        ]
        allocations = allocate_message_ids(messages)

        # String sort: MSG_1 < MSG_10 < MSG_2
        assert allocations["MSG_1"] == 0
        assert allocations["MSG_10"] == 1
        assert allocations["MSG_2"] == 2

    def test_empty_name_handled(self) -> None:
        """Empty message name should not crash."""
        msg = Message(
            description="Empty name message",
            fields=[PrimitiveField("id", type_name=Type.UINT8)],
        )
        msg.name = ""

        allocations = allocate_message_ids([msg])
        assert "" in allocations

    def test_case_sensitive_sorting(self) -> None:
        """Sorting should be case-sensitive (uppercase < lowercase in ASCII)."""
        messages = [
            _create_message("msg_lower"),
            _create_message("MSG_UPPER"),
        ]
        allocations = allocate_message_ids(messages)

        # ASCII: uppercase < lowercase
        assert allocations["MSG_UPPER"] < allocations["msg_lower"]
