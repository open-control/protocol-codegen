"""
Encoding strategies for protocol-specific size calculations and code generation.

This package provides the Strategy Pattern implementation for handling
the different encoding requirements of Serial8 (8-bit) and SysEx (7-bit) protocols.

Components:
- EncodingStrategy: Abstract base class for encoding calculations
- IntegerEncodingSpec, NormEncodingSpec, StringEncodingSpec: Data specs for code generation
- Serial8EncodingStrategy: 8-bit binary encoding (no expansion)
- SysExEncodingStrategy: 7-bit MIDI-safe encoding (with expansion)
"""

from .serial8_strategy import Serial8EncodingStrategy
from .strategy import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)
from .sysex_strategy import SysExEncodingStrategy


def get_encoding_strategy(protocol: str) -> EncodingStrategy:
    """
    Get encoding strategy for protocol.

    Args:
        protocol: Protocol name ('serial8' or 'sysex')

    Returns:
        Appropriate EncodingStrategy implementation

    Raises:
        ValueError: If protocol is unknown
    """
    if protocol == "serial8":
        return Serial8EncodingStrategy()
    elif protocol == "sysex":
        return SysExEncodingStrategy()
    else:
        raise ValueError(f"Unknown protocol: {protocol}")


__all__ = [
    # Base classes and specs
    "EncodingStrategy",
    "IntegerEncodingSpec",
    "NormEncodingSpec",
    "StringEncodingSpec",
    # Implementations
    "Serial8EncodingStrategy",
    "SysExEncodingStrategy",
    # Factory
    "get_encoding_strategy",
]
