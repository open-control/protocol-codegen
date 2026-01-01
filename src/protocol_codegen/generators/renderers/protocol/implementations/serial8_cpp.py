"""Serial8 C++ Protocol Renderer."""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.framings.serial8 import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.languages.cpp import (
    CppProtocolMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


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
