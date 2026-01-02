"""Serial8 C++ Protocol Renderer."""

from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
from protocol_codegen.generators.compositions.registry import register_renderer
from protocol_codegen.generators.languages.cpp.protocol_mixin import (
    CppProtocolMixin,
)
from protocol_codegen.generators.protocols.serial8.framing import (
    Serial8FramingMixin,
)


@register_renderer("protocol", "cpp", "serial8")
class Serial8CppProtocolRenderer(
    CppProtocolMixin,
    Serial8FramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.hpp.template renderer for Serial8 + C++.

    Combines:
    - CppProtocolMixin: C++ syntax
    - Serial8FramingMixin: COBS/Serial framing
    - ProtocolRendererBase: Assembly logic
    """

    pass


__all__ = ["Serial8CppProtocolRenderer"]
