"""
Binary Protocol Configuration for Sensor Network Example

This file configures the Binary protocol parameters.
"""

from protocol_codegen.generators.orchestrators.binary import (
    BinaryConfig,
    BinaryLimits,
)

# Binary Configuration
PROTOCOL_CONFIG = BinaryConfig(
    limits=BinaryLimits(
        max_message_size=4096,  # Maximum message size (larger than SysEx)
    ),
)
