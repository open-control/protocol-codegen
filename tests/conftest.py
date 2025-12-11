"""
Pytest fixtures for protocol-codegen tests.

Provides reusable test fixtures for TypeRegistry, Messages, and Fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from protocol_codegen.core.field import (
    CompositeField,
    PrimitiveField,
    Type,
    populate_type_names,
)
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def setup_type_enum() -> Generator[None]:
    """
    Populate Type enum before each test.

    This fixture runs automatically for all tests to ensure the Type enum
    is properly populated with builtin type names.
    """
    registry = TypeRegistry()
    registry.load_builtins()
    populate_type_names(list(registry.types.keys()))
    yield
    # Cleanup: clear enum for isolation between tests
    Type._member_map_.clear()
    Type._member_names_ = []
    Type._value2member_map_.clear()


@pytest.fixture
def type_registry() -> TypeRegistry:
    """
    Provide a fresh TypeRegistry with builtin types loaded.

    Returns:
        TypeRegistry instance with all builtin types available.
    """
    registry = TypeRegistry()
    registry.load_builtins()
    return registry


@pytest.fixture
def sample_primitive_fields() -> list[PrimitiveField]:
    """
    Provide sample primitive fields for testing.

    Returns:
        List of common primitive field definitions.
    """
    return [
        PrimitiveField("sensorId", type_name=Type.UINT8),
        PrimitiveField("value", type_name=Type.FLOAT32),
        PrimitiveField("timestamp", type_name=Type.UINT32),
        PrimitiveField("name", type_name=Type.STRING),
        PrimitiveField("isActive", type_name=Type.BOOL),
    ]


@pytest.fixture
def sample_array_field() -> PrimitiveField:
    """
    Provide a sample array field for testing.

    Returns:
        PrimitiveField with array size specified.
    """
    return PrimitiveField("values", type_name=Type.UINT8, array=8)


@pytest.fixture
def sample_dynamic_array_field() -> PrimitiveField:
    """
    Provide a sample dynamic array field for testing.

    Returns:
        PrimitiveField with dynamic=True for std::vector generation.
    """
    return PrimitiveField("dynamicValues", type_name=Type.FLOAT32, array=16, dynamic=True)


@pytest.fixture
def sample_composite_field() -> CompositeField:
    """
    Provide a sample composite field for testing.

    Returns:
        CompositeField with nested primitive fields.
    """
    return CompositeField(
        "reading",
        fields=[
            PrimitiveField("id", type_name=Type.UINT8),
            PrimitiveField("value", type_name=Type.FLOAT32),
        ],
    )


@pytest.fixture
def sample_composite_array_field() -> CompositeField:
    """
    Provide a sample composite array field for testing.

    Returns:
        CompositeField with array size for struct array generation.
    """
    return CompositeField(
        "readings",
        fields=[
            PrimitiveField("id", type_name=Type.UINT8),
            PrimitiveField("value", type_name=Type.FLOAT32),
        ],
        array=8,
    )


@pytest.fixture
def sample_message() -> Message:
    """
    Provide a sample message for testing.

    Returns:
        Message with common field types.
    """
    msg = Message(
        description="Test sensor reading message",
        fields=[
            PrimitiveField("sensorId", type_name=Type.UINT8),
            PrimitiveField("value", type_name=Type.FLOAT32),
        ],
    )
    msg.name = "SENSOR_READING"
    return msg


@pytest.fixture
def sample_messages() -> list[Message]:
    """
    Provide multiple sample messages for testing ID allocation.

    Returns:
        List of messages with different names for deterministic ordering tests.
    """
    messages: list[Message] = []

    # Create messages with names that will sort in a specific order
    names_and_fields: list[tuple[str, str, list[PrimitiveField]]] = [
        ("ZEBRA_MESSAGE", "Z message", [PrimitiveField("id", type_name=Type.UINT8)]),
        ("ALPHA_MESSAGE", "A message", [PrimitiveField("id", type_name=Type.UINT8)]),
        ("MIDDLE_MESSAGE", "M message", [PrimitiveField("id", type_name=Type.UINT8)]),
    ]

    for name, desc, fields in names_and_fields:
        msg = Message(description=desc, fields=fields)
        msg.name = name
        messages.append(msg)

    return messages
