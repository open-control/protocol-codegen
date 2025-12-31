"""
Encoding strategies for protocol-specific size calculations.

This package provides the Strategy Pattern implementation for handling
the different encoding requirements of Serial8 (8-bit) and SysEx (7-bit) protocols.
"""

from .serial8_strategy import Serial8EncodingStrategy
from .strategy import EncodingStrategy
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
    "EncodingStrategy",
    "Serial8EncodingStrategy",
    "SysExEncodingStrategy",
    "get_encoding_strategy",
]
