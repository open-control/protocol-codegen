"""
Protocol-specific encoding and framing strategies.

This module contains the protocol axis of the code generation:
- base: EncodingStrategy abstract base class
- binary: 8-bit binary encoding
- sysex: 7-bit MIDI SysEx encoding
"""

from protocol_codegen.generators.protocols.base import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)
from protocol_codegen.generators.protocols.binary import (
    BinaryEncodingStrategy,
    BinaryFramingMixin,
)
from protocol_codegen.generators.protocols.sysex import (
    SysExEncodingStrategy,
    SysExFramingMixin,
)

__all__ = [
    # Base classes
    "EncodingStrategy",
    "IntegerEncodingSpec",
    "NormEncodingSpec",
    "StringEncodingSpec",
    # Binary protocol
    "BinaryEncodingStrategy",
    "BinaryFramingMixin",
    # SysEx protocol
    "SysExEncodingStrategy",
    "SysExFramingMixin",
    # Factory function
    "get_encoding_strategy",
]


def get_encoding_strategy(protocol: str) -> EncodingStrategy:
    """Factory function to get an encoding strategy by protocol name.

    Args:
        protocol: Protocol identifier ('binary', 'sysex')

    Returns:
        Protocol-specific EncodingStrategy instance

    Raises:
        ValueError: If protocol is not supported
    """
    strategies = {
        "binary": BinaryEncodingStrategy,
        "sysex": SysExEncodingStrategy,
    }

    strategy_class = strategies.get(protocol.lower())
    if strategy_class is None:
        supported = ", ".join(sorted(strategies.keys()))
        raise ValueError(f"Unknown protocol '{protocol}'. Supported: {supported}")

    return strategy_class()
