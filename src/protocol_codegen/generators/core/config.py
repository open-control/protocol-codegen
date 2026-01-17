"""
Common Protocol Configuration Types.

Shared TypedDict definitions for protocol configuration across all backends.
"""

from typing import TypedDict


class StructureConfig(TypedDict):
    """Binary structure configuration."""

    message_type_offset: int
    payload_offset: int


class SysExFramingConfig(TypedDict):
    """SysEx framing configuration."""

    start: int
    end: int
    manufacturer_id: int
    device_id: int
    min_message_length: int
    message_type_offset: int
    payload_offset: int


class LimitsConfig(TypedDict):
    """Protocol limits configuration."""

    string_max_length: int
    array_max_items: int
    max_payload_size: int
    max_message_size: int


class ProtocolConfig(TypedDict, total=False):
    """
    Unified protocol configuration.

    Used by constants generators for both C++ and Java.
    - Binary uses: structure + limits
    - SysEx uses: sysex + limits
    """

    structure: StructureConfig  # Binary
    sysex: SysExFramingConfig  # SysEx
    limits: LimitsConfig
