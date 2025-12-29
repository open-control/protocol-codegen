"""
Method naming utilities for protocol generation.

Converts message names to method/callback names following consistent conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from protocol_codegen.core.field import FieldBase


# Suffixes to remove from message names for cleaner method names
_REMOVABLE_SUFFIXES = ("_BY_INDEX", "_CHANGE", "_MESSAGE")

# Fields to exclude from method parameters (implicit or deprecated)
_EXCLUDED_FIELDS = frozenset({"fromHost", "isEcho"})


def message_name_to_method_name(message_name: str) -> str:
    """
    Convert MESSAGE_NAME to methodName.

    Removes common suffixes for cleaner API.

    Examples:
        TRANSPORT_PLAY -> transportPlay
        DEVICE_SELECT_BY_INDEX -> deviceSelect
        REQUEST_DEVICE_LIST_WINDOW -> requestDeviceListWindow
        DEVICE_REMOTE_CONTROL_VALUE_CHANGE -> deviceRemoteControlValue
    """
    name = message_name
    for suffix in _REMOVABLE_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break  # Only remove one suffix

    return to_camel_case(name)


def message_name_to_callback_name(message_name: str) -> str:
    """
    Convert MESSAGE_NAME to onMethodName callback.

    Examples:
        TRANSPORT_PLAY -> onTransportPlay
        DEVICE_LIST_RESPONSE -> onDeviceListResponse
    """
    method = message_name_to_method_name(message_name)
    return f"on{method[0].upper()}{method[1:]}"


def to_camel_case(screaming_snake: str) -> str:
    """
    Convert SCREAMING_SNAKE_CASE to camelCase.

    Examples:
        TRANSPORT_PLAY -> transportPlay
        DEVICE_INDEX -> deviceIndex
    """
    parts = screaming_snake.lower().split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def to_pascal_case(screaming_snake: str) -> str:
    """
    Convert SCREAMING_SNAKE_CASE to PascalCase.

    Examples:
        TRANSPORT_PLAY -> TransportPlay
        DEVICE_INDEX -> DeviceIndex
    """
    return "".join(word.capitalize() for word in screaming_snake.lower().split("_"))


def get_excluded_fields() -> frozenset[str]:
    """Return the set of field names to exclude from method parameters."""
    return _EXCLUDED_FIELDS


def should_exclude_field(field_name: str) -> bool:
    """Check if a field should be excluded from method parameters."""
    return field_name in _EXCLUDED_FIELDS
