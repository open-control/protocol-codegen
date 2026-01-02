"""
Serial8 Protocol Components.

Provides Serial8-specific implementations of protocol components:
- Serial8EncodingStrategy for 8-bit binary encoding
- Serial8 Protocol Renderers for C++ and Java
"""

from __future__ import annotations

from protocol_codegen.generators.orchestrators.protocol_components import ProtocolComponents
from protocol_codegen.generators.protocols.serial8 import Serial8EncodingStrategy
from protocol_codegen.generators.renderers.protocol import (
    Serial8CppProtocolRenderer,
    Serial8JavaProtocolRenderer,
)


class Serial8Components(ProtocolComponents):
    """
    Serial8 protocol components.

    Provides 8-bit binary encoding strategy and protocol renderers
    for USB Serial communication with COBS framing.
    """

    def get_encoding_strategy(self) -> Serial8EncodingStrategy:
        """Return Serial8 8-bit binary encoding strategy."""
        return Serial8EncodingStrategy()

    def get_cpp_protocol_renderer(self) -> Serial8CppProtocolRenderer:
        """Return Serial8 C++ Protocol.hpp.template renderer."""
        return Serial8CppProtocolRenderer()

    def get_java_protocol_renderer(self, package: str) -> Serial8JavaProtocolRenderer:
        """Return Serial8 Java Protocol.java.template renderer."""
        return Serial8JavaProtocolRenderer(package=package)


__all__ = ["Serial8Components"]
