"""SysEx C++ Protocol Renderer."""

from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.framings.sysex import (
    SysExFramingMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.languages.cpp import (
    CppProtocolMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "cpp", "sysex")
class SysExCppProtocolRenderer(
    CppProtocolMixin,
    SysExFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.hpp.template renderer for SysEx + C++.
    """

    pass


__all__ = ["SysExCppProtocolRenderer"]
