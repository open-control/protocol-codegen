"""Binary Java Protocol Renderer."""

from protocol_codegen.generators.compositions.protocol_base import ProtocolRendererBase
from protocol_codegen.generators.compositions.registry import register_renderer
from protocol_codegen.generators.languages.java.protocol_mixin import (
    JavaProtocolMixin,
)
from protocol_codegen.generators.protocols.binary.framing import (
    BinaryFramingMixin,
)


@register_renderer("protocol", "java", "binary")
class BinaryJavaProtocolRenderer(
    JavaProtocolMixin,
    BinaryFramingMixin,
    ProtocolRendererBase,
):
    """
    Protocol.java.template renderer for Binary + Java.
    """

    def __init__(self, package: str = "protocol") -> None:
        JavaProtocolMixin.__init__(self, package)


__all__ = ["BinaryJavaProtocolRenderer"]
