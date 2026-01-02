"""
Serial8 Protocol Configuration for Sensor Network Example

This file configures the Serial8 protocol parameters.
"""

from protocol_codegen.generators.orchestrators.serial8 import (
    Serial8Config,
    Serial8Limits,
)

# Serial8 Configuration
PROTOCOL_CONFIG = Serial8Config(
    limits=Serial8Limits(
        max_message_size=4096,  # Maximum message size (larger than SysEx)
    ),
)
