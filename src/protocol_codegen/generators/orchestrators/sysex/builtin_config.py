"""
Builtin SysEx Configuration (Pure Python, Type-Safe)

Default configuration for SysEx protocol constants.
No YAML - everything defined in Python with strong typing.

This replaces sysex_protocol_config.yaml with pure Python configuration.
"""

from .config import SysExConfig, SysExFraming, SysExLimits, SysExStructure

# Default configuration instance
BUILTIN_SYSEX_CONFIG = SysExConfig(
    framing=SysExFraming(
        start=0xF0,  # MIDI SysEx start byte
        end=0xF7,  # MIDI SysEx end byte
        manufacturer_id=0x7D,  # Educational/development use
        device_id=0x00,  # All devices
    ),
    structure=SysExStructure(
        min_message_length=5,  # [F0 MID DID TYPE F7] = 5 bytes minimum
        message_type_offset=3,  # After start, mfr_id, dev_id
        payload_offset=4,  # After message_type
    ),
    limits=SysExLimits(
        # string_max_length and array_max_items use protocol defaults (127)
        max_payload_size=512,  # Max payload bytes
        max_message_size=1024,  # Max total message size
    ),
)
