"""
Protocol.java.template Generator for Serial8

Generates a minimal Protocol class template with:
- Zero-allocation streaming encode pattern
- Reflection cache for performance
- UDP transport only (essential)

The consumer adapts for their environment and adds metrics if needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_protocol_template_java(
    messages: list[Message], output_path: Path, package: str
) -> str:
    """
    Generate Protocol.java.template for Serial8 transport.

    Args:
        messages: List of message definitions
        output_path: Where to write Protocol.java.template
        package: Java package name

    Returns:
        Generated Java template code
    """
    code = f"""package {package};

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Protocol - Serial8 Protocol Handler (UDP)
 *
 * Zero-allocation encoding via encode(buffer, offset).
 * Extend ProtocolCallbacks for typed message callbacks.
 */
public class Protocol extends ProtocolCallbacks {{

    private final DatagramSocket socket;
    private final InetAddress address;
    private final int port;

    // Reflection cache: encode(byte[], int) -> bytes written
    private record MessageMeta(MessageID messageId, Method encodeMethod) {{}}
    private final ConcurrentHashMap<Class<?>, MessageMeta> messageCache = new ConcurrentHashMap<>();

    // Pre-allocated send buffer
    private static final int BUFFER_SIZE = 4096;
    private final byte[] sendBuffer = new byte[BUFFER_SIZE];

    public Protocol(String host, int port) throws Exception {{
        this.socket = new DatagramSocket();
        this.address = InetAddress.getByName(host);
        this.port = port;
    }}

    public <T> void send(T message) {{
        if (message == null || socket.isClosed()) return;

        MessageMeta meta = messageCache.computeIfAbsent(message.getClass(), c -> {{
            try {{
                Field idField = c.getField("MESSAGE_ID");
                MessageID id = (MessageID) idField.get(null);
                Method encode = c.getMethod("encode", byte[].class, int.class);
                return new MessageMeta(id, encode);
            }} catch (Exception e) {{
                throw new RuntimeException("Failed to cache: " + c.getName(), e);
            }}
        }});

        try {{
            sendBuffer[0] = meta.messageId().getValue();
            int payloadLen = (int) meta.encodeMethod().invoke(message, sendBuffer, 1);
            int frameLen = 1 + payloadLen;

            socket.send(new DatagramPacket(sendBuffer, 0, frameLen, address, port));
        }} catch (Exception e) {{
            // Handle error as needed
        }}
    }}

    public void dispatch(byte[] frame) {{
        if (frame == null || frame.length < ProtocolConstants.MIN_MESSAGE_LENGTH) return;

        byte idByte = frame[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID id = MessageID.fromValue(idByte);
        if (id == null) return;

        int payloadLen = frame.length - ProtocolConstants.PAYLOAD_OFFSET;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(frame, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        DecoderRegistry.dispatch(this, id, payload);
    }}

    public void close() {{
        socket.close();
    }}

    public boolean isConnected() {{
        return socket != null && !socket.isClosed();
    }}
}}
"""

    return code
