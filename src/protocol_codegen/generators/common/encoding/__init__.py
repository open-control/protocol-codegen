"""
Encoding strategies - Re-exports from generators.protocols.

NOTE: This module is deprecated. Import directly from:
- generators.protocols.base (EncodingStrategy, specs)
- generators.protocols.serial8 (Serial8EncodingStrategy)
- generators.protocols.sysex (SysExEncodingStrategy)
- generators.core.encoding_ops (ByteWriteOp, MethodSpec, etc.)
"""

# Re-export for backward compatibility
from protocol_codegen.generators.core.encoding_ops import (
    ByteReadOp,
    ByteWriteOp,
    DecoderMethodSpec,
    MethodSpec,
)
from protocol_codegen.generators.protocols import (
    EncodingStrategy,
    IntegerEncodingSpec,
    NormEncodingSpec,
    StringEncodingSpec,
)
from protocol_codegen.generators.protocols.serial8 import Serial8EncodingStrategy
from protocol_codegen.generators.protocols.sysex import SysExEncodingStrategy


def get_encoding_strategy(protocol: str) -> EncodingStrategy:
    """Get encoding strategy for protocol."""
    if protocol == "serial8":
        return Serial8EncodingStrategy()
    elif protocol == "sysex":
        return SysExEncodingStrategy()
    else:
        raise ValueError(f"Unknown protocol: {protocol}")


__all__ = [
    "EncodingStrategy",
    "IntegerEncodingSpec",
    "NormEncodingSpec",
    "StringEncodingSpec",
    "ByteWriteOp",
    "MethodSpec",
    "ByteReadOp",
    "DecoderMethodSpec",
    "Serial8EncodingStrategy",
    "SysExEncodingStrategy",
    "get_encoding_strategy",
]
