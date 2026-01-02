"""
SysEx Framing Mixin for Protocol Renderers.

Provides SysEx MIDI protocol framing (F0...F7).
"""


class SysExFramingMixin:
    """
    Mixin providing SysEx framing for protocol templates.

    Wire format: [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][payload...][F7]
    All payload bytes must be < 0x80 (7-bit encoding)

    Expected to be combined with a LanguageMixin that provides is_cpp, is_java,
    render_memcpy, render_arraycopy, and render_cast_message_id.
    """

    @property
    def protocol_name(self) -> str:
        return "SysEx"

    @property
    def transport_description(self) -> str:
        return "MIDI SysEx"

    @property
    def default_transport_type(self) -> str:
        if self.is_cpp:
            return "IMidiTransport"
        return "MidiOut"

    def render_framing_constants(self) -> str:
        """Render protocol-specific constants usage."""
        if self.is_cpp:
            return """        using Protocol::SYSEX_START;
        using Protocol::SYSEX_END;
        using Protocol::MANUFACTURER_ID;
        using Protocol::DEVICE_ID;
        using Protocol::MAX_MESSAGE_SIZE;
"""
        return ""

    def render_frame_build(self) -> str:
        """Render frame building code (send path)."""
        if self.is_cpp:
            return f"""
        // SysEx frame: [F0][MANUF][DEVICE][MessageID][payload...][F7]
        frame[offset++] = SYSEX_START;
        frame[offset++] = MANUFACTURER_ID;
        frame[offset++] = DEVICE_ID;
        frame[offset++] = {self.render_cast_message_id()};
        {self.render_memcpy("frame + offset", "payload", "payloadLen")}
        offset += payloadLen;
        frame[offset++] = SYSEX_END;
"""
        else:
            return f"""
            // SysEx frame: [F0][MANUF][DEVICE][MessageID][payload...][F7]
            frame[offset++] = ProtocolConstants.SYSEX_START;
            frame[offset++] = ProtocolConstants.MANUFACTURER_ID;
            frame[offset++] = ProtocolConstants.DEVICE_ID;
            frame[offset++] = (byte) {self.render_cast_message_id()};
            {self.render_arraycopy("payload", "0", "frame", "offset", "payload.length")}
            offset += payload.length;
            frame[offset++] = ProtocolConstants.SYSEX_END;
"""

    def render_frame_validate(self) -> str:
        """Render frame validation code (receive path)."""
        if self.is_cpp:
            return """        if (data == nullptr || len < MIN_MESSAGE_LENGTH) {
            return;
        }

        if (data[0] != SYSEX_START || data[len - 1] != SYSEX_END) {
            return;
        }

        if (data[1] != MANUFACTURER_ID || data[2] != DEVICE_ID) {
            return;
        }
"""
        else:
            return """        if (data == null || data.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {
            return;
        }

        if (data[0] != ProtocolConstants.SYSEX_START ||
            data[data.length - 1] != ProtocolConstants.SYSEX_END) {
            return;
        }

        if (data[1] != ProtocolConstants.MANUFACTURER_ID ||
            data[2] != ProtocolConstants.DEVICE_ID) {
            return;
        }
"""

    def render_frame_parse(self) -> str:
        """Render frame parsing code (receive path)."""
        if self.is_cpp:
            return """
        MessageID messageId = static_cast<MessageID>(data[MESSAGE_TYPE_OFFSET]);
        uint16_t payloadLen = len - MIN_MESSAGE_LENGTH;
        const uint8_t* payload = data + PAYLOAD_OFFSET;

        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
"""
        else:
            return """
        byte idByte = data[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(idByte);
        if (messageId == null) return;

        int payloadLen = data.length - ProtocolConstants.MIN_MESSAGE_LENGTH;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(data, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        DecoderRegistry.dispatch(this, messageId, payload);
"""

    def render_transport_includes(self) -> str:
        """Render transport-specific includes."""
        if self.is_cpp:
            return ""  # SysEx typically uses existing MIDI includes
        return ""


__all__ = ["SysExFramingMixin"]
