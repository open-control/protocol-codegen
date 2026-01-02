"""
SysEx Protocol Configuration for Sensor Network Example

This file configures the SysEx protocol parameters.
"""

from protocol_codegen.generators.orchestrators.sysex import (
    SysExConfig,
    SysExFraming,
    SysExLimits,
)

# SysEx Configuration
PROTOCOL_CONFIG = SysExConfig(
    framing=SysExFraming(
        manufacturer_id=0x7D,  # Educational/Development use (0x7D = 125)
        device_id=0x42,  # Custom device ID
    ),
    limits=SysExLimits(
        # string_max_length and array_max_items use protocol defaults (127)
        max_message_size=512,  # Maximum SysEx message size
    ),
)
