"""Serial8 Java Protocol Renderer."""

from protocol_codegen.generators.languages.java.protocol_mixin import (
    JavaProtocolMixin,
)
from protocol_codegen.generators.protocols.serial8.framing import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.protocol.base import ProtocolRendererBase
from protocol_codegen.generators.renderers.registry import register_renderer


@register_renderer("protocol", "java", "serial8")
class Serial8JavaProtocolRenderer(
    JavaProtocolMixin,
    Serial8FramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.java.template renderer for Serial8 + Java.
    """

    def __init__(self, package: str = "protocol") -> None:
        JavaProtocolMixin.__init__(self, package)


__all__ = ["Serial8JavaProtocolRenderer"]
