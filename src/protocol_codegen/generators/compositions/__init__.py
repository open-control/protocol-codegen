"""
Protocol × Language Compositions.

This module contains the concrete compositions of protocol strategies
and language backends that form complete renderers.

Available compositions:
- Serial8CppRenderer: Serial8 protocol + C++ language
- Serial8JavaRenderer: Serial8 protocol + Java language
- SysExCppRenderer: SysEx protocol + C++ language
- SysExJavaRenderer: SysEx protocol + Java language
"""

from protocol_codegen.generators.compositions.base import ProtocolRenderer
from protocol_codegen.generators.compositions.registry import RendererRegistry
from protocol_codegen.generators.compositions.serial8_cpp import Serial8CppRenderer
from protocol_codegen.generators.compositions.serial8_java import Serial8JavaRenderer
from protocol_codegen.generators.compositions.sysex_cpp import SysExCppRenderer
from protocol_codegen.generators.compositions.sysex_java import SysExJavaRenderer

__all__ = [
    # Base classes
    "ProtocolRenderer",
    "RendererRegistry",
    # Compositions
    "Serial8CppRenderer",
    "Serial8JavaRenderer",
    "SysExCppRenderer",
    "SysExJavaRenderer",
]
