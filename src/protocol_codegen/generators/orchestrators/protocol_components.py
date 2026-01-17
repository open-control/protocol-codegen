"""
Protocol Components Interface.

Defines the abstract interface for protocol-specific components.
Each protocol (Binary, SysEx, etc.) implements this interface
to provide its specific encoding strategy and renderers.

This enables the unified BaseProtocolGenerator to work with any protocol
without code duplication.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
    from protocol_codegen.generators.protocols import EncodingStrategy


class ProtocolComponents(ABC):
    """
    Abstract interface for protocol-specific components.

    Each protocol implementation (Binary, SysEx, etc.) must provide:
    - An encoding strategy for byte-level encoding/decoding
    - Protocol renderers for generating Protocol.hpp/java templates

    This abstraction allows BaseProtocolGenerator to be protocol-agnostic
    while delegating protocol-specific behavior to implementations.

    Example usage:
        class BinaryComponents(ProtocolComponents):
            def get_encoding_strategy(self) -> EncodingStrategy:
                return BinaryEncodingStrategy()
            ...
    """

    @abstractmethod
    def get_encoding_strategy(self) -> EncodingStrategy:
        """
        Return the encoding strategy for this protocol.

        The encoding strategy defines how values are encoded to bytes
        (e.g., 8-bit binary for Binary, 7-bit for SysEx).

        Returns:
            Protocol-specific EncodingStrategy instance
        """
        ...

    @abstractmethod
    def get_cpp_protocol_renderer(self) -> ProtocolRendererBase:
        """
        Return the C++ Protocol.hpp.template renderer.

        Returns:
            Instance of the C++ protocol renderer for this protocol
        """
        ...

    @abstractmethod
    def get_java_protocol_renderer(self, package: str) -> ProtocolRendererBase:
        """
        Return the Java Protocol.java.template renderer.

        Args:
            package: Java package name for the generated class

        Returns:
            Instance of the Java protocol renderer for this protocol
        """
        ...


__all__ = ["ProtocolComponents"]
