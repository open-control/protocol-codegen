"""
Serial8 Protocol - 8-bit binary encoding.

Components:
- Serial8EncodingStrategy: Encoding calculations for 8-bit protocol
- Serial8FramingMixin: Framing logic for protocol renderers
"""

from protocol_codegen.generators.protocols.serial8.encoding import (
    Serial8EncodingStrategy,
)
from protocol_codegen.generators.protocols.serial8.framing import Serial8FramingMixin

__all__ = [
    "Serial8EncodingStrategy",
    "Serial8FramingMixin",
]
