"""
Binary Protocol Components.

Provides Binary-specific implementations of protocol components:
- BinaryEncodingStrategy for 8-bit binary encoding
- Binary Protocol Renderers for C++ and Java
"""

from __future__ import annotations

from protocol_codegen.generators.compositions import (
    BinaryCppProtocolRenderer,
    BinaryJavaProtocolRenderer,
)
from protocol_codegen.generators.orchestrators.protocol_components import ProtocolComponents
from protocol_codegen.generators.protocols.binary import BinaryEncodingStrategy


class BinaryComponents(ProtocolComponents):
    """
    Binary protocol components.

    Provides 8-bit binary encoding strategy and protocol renderers
    for USB Serial communication with COBS framing.
    """

    def get_encoding_strategy(self) -> BinaryEncodingStrategy:
        """Return Binary 8-bit binary encoding strategy."""
        return BinaryEncodingStrategy()

    def get_cpp_protocol_renderer(self) -> BinaryCppProtocolRenderer:
        """Return Binary C++ Protocol.hpp.template renderer."""
        return BinaryCppProtocolRenderer()

    def get_java_protocol_renderer(self, package: str) -> BinaryJavaProtocolRenderer:
        """Return Binary Java Protocol.java.template renderer."""
        return BinaryJavaProtocolRenderer(package=package)


__all__ = ["BinaryComponents"]
