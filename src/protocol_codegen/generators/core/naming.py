"""
Method naming utilities for protocol generation.

Converts message names to method/callback names following consistent conventions.
No dynamic transformations - message names should be correctly defined at source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# Fields to exclude from method parameters (if any)
# Note: fromHost and isEcho were removed as part of protocol simplification
_EXCLUDED_FIELDS: frozenset[str] = frozenset()


def message_name_to_method_name(message_name: str) -> str:
    """
    Convert MESSAGE_NAME to methodName.

    Direct conversion without suffix manipulation.
    Message names should be correctly defined at source.

    Examples:
        TRANSPORT_PLAY -> transportPlay
        DEVICE_SELECT -> deviceSelect
        TRACK_VOLUME_STATE -> trackVolumeState
    """
    return to_camel_case(message_name)


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


def capitalize_first(s: str) -> str:
    """
    Capitalize first letter only.

    Examples:
        uint8 → Uint8
        float32 → Float32
    """
    if not s:
        return s
    return s[0].upper() + s[1:]


def field_to_pascal_case(field_name: str) -> str:
    """
    Convert camelCase field name to PascalCase.

    This is used for inner struct/class names derived from field names.

    Examples:
        pageInfo → PageInfo
        remoteControls → RemoteControls
        deviceName → DeviceName
    """
    if not field_name:
        return field_name
    return field_name[0].upper() + field_name[1:]
