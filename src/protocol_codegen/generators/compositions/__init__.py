"""
Protocol × Language Compositions.

This module contains the concrete compositions of protocol strategies
and language backends that form complete renderers.

Available compositions:
- Serial8CppProtocolRenderer: Serial8 protocol + C++ language
- Serial8JavaProtocolRenderer: Serial8 protocol + Java language
- SysExCppProtocolRenderer: SysEx protocol + C++ language
- SysExJavaProtocolRenderer: SysEx protocol + Java language
"""

from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
from protocol_codegen.generators.compositions.registry import RendererRegistry
from protocol_codegen.generators.compositions.serial8_cpp import (
    Serial8CppProtocolRenderer,
)
from protocol_codegen.generators.compositions.serial8_java import (
    Serial8JavaProtocolRenderer,
)
from protocol_codegen.generators.compositions.sysex_cpp import SysExCppProtocolRenderer
from protocol_codegen.generators.compositions.sysex_java import SysExJavaProtocolRenderer

__all__ = [
    # Base classes
    "ProtocolRendererBase",
    "RendererRegistry",
    # Compositions
    "Serial8CppProtocolRenderer",
    "Serial8JavaProtocolRenderer",
    "SysExCppProtocolRenderer",
    "SysExJavaProtocolRenderer",
]
