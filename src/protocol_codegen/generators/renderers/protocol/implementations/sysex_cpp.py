"""SysEx C++ Protocol Renderer."""

from protocol_codegen.generators.languages.cpp.protocol_mixin import (
    CppProtocolMixin,
)
from protocol_codegen.generators.protocols.sysex.framing import (
    SysExFramingMixin,
)
from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
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
