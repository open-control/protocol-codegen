"""
Protocol-specific encoding and framing strategies.

This module contains the protocol axis of the code generation:
- base: EncodingStrategy abstract base class
- serial8: 8-bit binary encoding
- sysex: 7-bit MIDI SysEx encoding
"""

from protocol_codegen.generators.protocols.base import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)

__all__ = [
    # Base classes
    "EncodingStrategy",
    "IntegerEncodingSpec",
    "NormEncodingSpec",
    "StringEncodingSpec",
]
