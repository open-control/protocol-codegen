"""
Binary Protocol - 8-bit binary encoding.

Components:
- BinaryEncodingStrategy: Encoding calculations for 8-bit protocol
- BinaryFramingMixin: Framing logic for protocol renderers
"""

from protocol_codegen.generators.protocols.binary.encoding import (
    BinaryEncodingStrategy,
)
from protocol_codegen.generators.protocols.binary.framing import BinaryFramingMixin

__all__ = [
    "BinaryEncodingStrategy",
    "BinaryFramingMixin",
]
