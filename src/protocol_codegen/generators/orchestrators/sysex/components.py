"""
SysEx Protocol Components.

Provides SysEx-specific implementations of protocol components:
- SysExEncodingStrategy for 7-bit MIDI encoding
- SysEx Protocol Renderers for C++ and Java
"""

from __future__ import annotations

from protocol_codegen.generators.compositions import (
    SysExCppProtocolRenderer,
    SysExJavaProtocolRenderer,
)
from protocol_codegen.generators.orchestrators.protocol_components import ProtocolComponents
from protocol_codegen.generators.protocols.sysex import SysExEncodingStrategy


class SysExComponents(ProtocolComponents):
    """
    SysEx protocol components.

    Provides 7-bit MIDI encoding strategy and protocol renderers
    for MIDI SysEx communication with F0...F7 framing.
    """

    def get_encoding_strategy(self) -> SysExEncodingStrategy:
        """Return SysEx 7-bit MIDI encoding strategy."""
        return SysExEncodingStrategy()

    def get_cpp_protocol_renderer(self) -> SysExCppProtocolRenderer:
        """Return SysEx C++ Protocol.hpp.template renderer."""
        return SysExCppProtocolRenderer()

    def get_java_protocol_renderer(self, package: str) -> SysExJavaProtocolRenderer:
        """Return SysEx Java Protocol.java.template renderer."""
        return SysExJavaProtocolRenderer(package=package)


__all__ = ["SysExComponents"]
