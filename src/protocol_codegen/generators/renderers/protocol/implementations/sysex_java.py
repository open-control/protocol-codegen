"""SysEx Java Protocol Renderer."""

from protocol_codegen.generators.protocols.sysex.framing import (
    SysExFramingMixin,
)
from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.protocol.mixins.languages.java import (
    JavaProtocolMixin,
)
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "java", "sysex")
class SysExJavaProtocolRenderer(
    JavaProtocolMixin,
    SysExFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.java.template renderer for SysEx + Java.
    """

    def __init__(self, package: str = "protocol") -> None:
        JavaProtocolMixin.__init__(self, package)


__all__ = ["SysExJavaProtocolRenderer"]
