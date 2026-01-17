"""
Protocol × Language Compositions.

This module contains the concrete compositions of protocol strategies
and language backends that form complete renderers.

Available compositions:
- BinaryCppProtocolRenderer: Binary protocol + C++ language
- BinaryJavaProtocolRenderer: Binary protocol + Java language
- SysExCppProtocolRenderer: SysEx protocol + C++ language
- SysExJavaProtocolRenderer: SysEx protocol + Java language
"""

from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
from protocol_codegen.generators.compositions.registry import RendererRegistry
from protocol_codegen.generators.compositions.binary_cpp import (
    BinaryCppProtocolRenderer,
)
from protocol_codegen.generators.compositions.binary_java import (
    BinaryJavaProtocolRenderer,
)
from protocol_codegen.generators.compositions.sysex_cpp import SysExCppProtocolRenderer
from protocol_codegen.generators.compositions.sysex_java import SysExJavaProtocolRenderer

__all__ = [
    # Base classes
    "ProtocolRendererBase",
    "RendererRegistry",
    # Compositions
    "BinaryCppProtocolRenderer",
    "BinaryJavaProtocolRenderer",
    "SysExCppProtocolRenderer",
    "SysExJavaProtocolRenderer",
]
