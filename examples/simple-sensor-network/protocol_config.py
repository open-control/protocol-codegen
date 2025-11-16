"""
SysEx Protocol Configuration for Sensor Network Example

This file configures the SysEx protocol parameters.
"""

from protocol_codegen.methods.sysex import SysExConfig, SysExLimits, SysExFraming

# SysEx Configuration
PROTOCOL_CONFIG = SysExConfig(
    framing=SysExFraming(
        manufacturer_id=0x7D,  # Educational/Development use (0x7D = 125)
        device_id=0x42,        # Custom device ID
    ),
    limits=SysExLimits(
        max_message_size=512,      # Maximum SysEx message size
        string_max_length=32,      # Maximum string length
        array_max_items=32          # Maximum array size
    )
)
