"""Binary C++ Protocol Renderer."""

from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
from protocol_codegen.generators.compositions.registry import register_renderer
from protocol_codegen.generators.languages.cpp.protocol_mixin import (
    CppProtocolMixin,
)
from protocol_codegen.generators.protocols.binary.framing import (
    BinaryFramingMixin,
)


@register_renderer("protocol", "cpp", "binary")
class BinaryCppProtocolRenderer(
    CppProtocolMixin,
    BinaryFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.hpp.template renderer for Binary + C++.

    Combines:
    - CppProtocolMixin: C++ syntax
    - BinaryFramingMixin: COBS/Serial framing
    - ProtocolRendererBase: Assembly logic
    """

    pass


__all__ = ["BinaryCppProtocolRenderer"]
