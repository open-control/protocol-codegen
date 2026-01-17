"""
Binary Framing Mixin for Protocol Renderers.

Provides Binary protocol framing (COBS, MessageID prefix).
"""

from typing import TYPE_CHECKING

# Type stubs for attributes provided by LanguageMixin at runtime
if TYPE_CHECKING:

    class _LanguageMixinStubs:
        """Stubs for type checking - provided by LanguageMixin at runtime."""

        @property
        def is_cpp(self) -> bool: ...

        @property
        def is_java(self) -> bool: ...

        def render_memcpy(self, dest: str, src: str, size: str) -> str: ...

        def render_arraycopy(
            self, src: str, src_pos: str, dest: str, dest_pos: str, length: str
        ) -> str: ...

        def render_cast_message_id(self) -> str: ...

    _FramingMixinBase = _LanguageMixinStubs
else:
    _FramingMixinBase = object


class BinaryFramingMixin(_FramingMixinBase):
    """
    Mixin providing Binary framing for protocol templates.

    Wire format: [MessageID][payload...]
    Framing: COBS handled by transport layer

    Expected to be combined with a LanguageMixin that provides is_cpp, is_java,
    render_memcpy, render_arraycopy, and render_cast_message_id.
    """

    @property
    def protocol_name(self) -> str:
        return "Binary"

    @property
    def transport_description(self) -> str:
        return "USB Serial with COBS framing"

    @property
    def default_transport_type(self) -> str:
        if self.is_cpp:
            return "oc::hal::IFrameTransport"
        return "IFrameTransport"

    def render_framing_constants(self) -> str:
        """Render protocol-specific constants usage."""
        if self.is_cpp:
            return """        using Protocol::MAX_MESSAGE_SIZE;
        using Protocol::MESSAGE_TYPE_OFFSET;
        using Protocol::PAYLOAD_OFFSET;
"""
        return ""

    def render_frame_build(self) -> str:
        """Render frame building code (send path)."""
        if self.is_cpp:
            return f"""
        // Binary frame: [MessageID][payload...]
        frame[offset++] = {self.render_cast_message_id()};
        {self.render_memcpy("frame + offset", "payload", "payloadLen")}
        offset += payloadLen;
"""
        else:
            return f"""
            // Binary frame: [MessageID][payload...]
            frame[offset++] = (byte) {self.render_cast_message_id()};
            {self.render_arraycopy("payload", "0", "frame", "offset", "payload.length")}
            offset += payload.length;
"""

    def render_frame_validate(self) -> str:
        """Render frame validation code (receive path)."""
        if self.is_cpp:
            return """        if (data == nullptr || len < MIN_MESSAGE_LENGTH) {
            return;
        }
"""
        else:
            return """        if (data == null || data.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {
            return;
        }
"""

    def render_frame_parse(self) -> str:
        """Render frame parsing code (receive path)."""
        if self.is_cpp:
            return """
        MessageID messageId = static_cast<MessageID>(data[MESSAGE_TYPE_OFFSET]);
        uint16_t payloadLen = len - PAYLOAD_OFFSET;
        const uint8_t* payload = data + PAYLOAD_OFFSET;

        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
"""
        else:
            return """
        byte idByte = data[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(idByte);
        if (messageId == null) return;

        int payloadLen = data.length - ProtocolConstants.PAYLOAD_OFFSET;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(data, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        DecoderRegistry.dispatch(this, messageId, payload);
"""

    def render_transport_includes(self) -> str:
        """Render transport-specific includes."""
        if self.is_cpp:
            return '#include <oc/hal/IFrameTransport.hpp>\n'
        return ""


__all__ = ["BinaryFramingMixin"]
