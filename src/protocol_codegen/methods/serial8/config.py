"""
Serial8 Protocol Configuration

Configuration for 8-bit serial binary protocol.
Uses full 8-bit byte range for maximum efficiency.
Framing (COBS) is handled by the bridge layer, not the codec.
"""

from pydantic import BaseModel, Field


class Serial8Limits(BaseModel):
    """Encoding limits for Serial8 protocol."""

    string_max_length: int = Field(
        default=255,
        ge=1,
        le=255,
        description="Maximum string length (8-bit length prefix)",
    )

    array_max_items: int = Field(
        default=255,
        ge=1,
        le=255,
        description="Maximum array items (8-bit count prefix)",
    )

    max_payload_size: int = Field(
        default=4096,
        ge=1,
        le=65535,
        description="Maximum payload size in bytes",
    )

    max_message_size: int = Field(
        default=4096,
        ge=1,
        le=65535,
        description="Maximum total message size in bytes",
    )

    include_message_name: bool = Field(
        default=False,
        description="Include message name prefix in payload for bridge logging",
    )


class Serial8Structure(BaseModel):
    """Message structure offsets for Serial8 protocol."""

    message_type_offset: int = Field(
        default=0,
        ge=0,
        description="Byte offset for message type ID",
    )

    payload_offset: int = Field(
        default=1,
        ge=0,
        description="Byte offset where payload starts",
    )


class Serial8Config(BaseModel):
    """Complete Serial8 protocol configuration."""

    limits: Serial8Limits = Field(default_factory=Serial8Limits)
    structure: Serial8Structure = Field(default_factory=Serial8Structure)

    model_config = {"frozen": True}
