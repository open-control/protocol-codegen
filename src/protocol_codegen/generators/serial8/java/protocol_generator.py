"""
Protocol.java.template Generator for Serial8

Generates a template Protocol class for UDP communication with oc-bridge.
The bridge handles COBS framing on the serial side; Java just sends/receives UDP packets.
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
    Generate Protocol.java.template for Serial8 transport (UDP).

    Args:
        messages: List of message definitions
        output_path: Where to write Protocol.java.template
        package: Java package name

    Returns:
        Generated Java template code
    """
    # Generate example callback assignments (TO_CONTROLLER messages - from controller)
    callback_examples: list[str] = []
    for message in messages[:5]:
        if message.is_to_controller():
            pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
            callback_name = f"on{pascal_name}"
            callback_examples.append(
                f"//     protocol.{callback_name} = msg -> {{ /* handle */ }};"
            )
    if not callback_examples:
        callback_examples.append("//     // Register callbacks here...")

    callback_examples_str = "\n".join(callback_examples)

    # Generate example API method calls (TO_HOST messages - to controller)
    method_examples: list[str] = []
    for message in messages[:5]:
        if message.is_to_host():
            parts = message.name.lower().split("_")
            method_name = parts[0] + "".join(word.capitalize() for word in parts[1:])
            method_examples.append(f"//     protocol.{method_name}(...);")
    if not method_examples:
        method_examples.append("//     // Call API methods here...")

    method_examples_str = "\n".join(method_examples)

    code = f"""package {package};

/**
 * Protocol.java.template - Serial8 Protocol Handler (UDP to oc-bridge)
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as YourProtocol.java
 * 2. Rename the class (e.g., BitwigProtocol)
 * 3. Implement UdpTransport or use existing implementation
 * 4. Wire transport receive callback to dispatch()
 *
 * Wire format: [MessageID][payload...]
 * Transport: UDP packets to oc-bridge (default port 9000)
 * Framing: Each UDP packet = one complete frame
 *
 * ============================================================================
 * ARCHITECTURE
 * ============================================================================
 *
 * YourProtocol extends ProtocolCallbacks
 *   - Callbacks: onMessageName members (inherited from ProtocolCallbacks)
 *   - API: explicit methods like transportPlayingState() (from ProtocolMethods)
 *   - send(): protected, called by API methods
 *   - dispatch(): called by transport on receive
 *
 * ============================================================================
 */

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.concurrent.ConcurrentHashMap;

public class YourProtocol extends ProtocolCallbacks {{

    // ========================================================================
    // Configuration
    // ========================================================================

    private static final String BRIDGE_HOST = "127.0.0.1";
    private static final int BRIDGE_PORT = 9000;

    // ========================================================================
    // Transport
    // ========================================================================

    private DatagramSocket socket;
    private InetAddress bridgeAddress;
    private int bridgePort;

    // Reflection cache for message encoding (zero-allocation after warmup)
    private record MessageMeta(MessageID messageId, Method encodeMethod) {{}}
    private final ConcurrentHashMap<Class<?>, MessageMeta> messageCache = new ConcurrentHashMap<>();

    // Pre-allocated send buffer
    private final byte[] sendBuffer = new byte[ProtocolConstants.MAX_MESSAGE_SIZE];

    // ========================================================================
    // Constructor
    // ========================================================================

    /**
     * Create protocol with default bridge address (127.0.0.1:9000)
     */
    public YourProtocol() throws Exception {{
        this(BRIDGE_HOST, BRIDGE_PORT);
    }}

    /**
     * Create protocol with specified bridge address
     *
     * @param host Bridge host address
     * @param port Bridge port
     */
    public YourProtocol(String host, int port) throws Exception {{
        this.socket = new DatagramSocket();
        this.bridgeAddress = InetAddress.getByName(host);
        this.bridgePort = port;

        // Start receive thread (for messages from bridge/controller)
        Thread receiveThread = new Thread(this::receiveLoop, "Protocol-Receive");
        receiveThread.setDaemon(true);
        receiveThread.start();
    }}

    // ========================================================================
    // Lifecycle
    // ========================================================================

    /**
     * Close the UDP socket
     */
    public void close() {{
        if (socket != null && !socket.isClosed()) {{
            socket.close();
        }}
    }}

    /**
     * Check if connected
     */
    public boolean isConnected() {{
        return socket != null && !socket.isClosed();
    }}

    // ========================================================================
    // Send (internal - called by ProtocolMethods)
    // ========================================================================

    /**
     * Send a protocol message (internal - called by explicit API methods)
     */
    @Override
    protected void send(Object message) {{
        if (message == null || socket.isClosed()) return;

        // Get or cache message metadata (reflection)
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
            // Build frame: [MessageID][payload...]
            sendBuffer[0] = meta.messageId().getValue();
            int payloadLen = (int) meta.encodeMethod().invoke(message, sendBuffer, 1);
            int frameLen = 1 + payloadLen;

            // Send UDP packet to bridge
            DatagramPacket packet = new DatagramPacket(
                sendBuffer, 0, frameLen, bridgeAddress, bridgePort
            );
            socket.send(packet);
        }} catch (Exception e) {{
            // Log error as appropriate for your project
            e.printStackTrace();
        }}
    }}

    // ========================================================================
    // Receive
    // ========================================================================

    /**
     * Receive loop - runs in background thread
     */
    private void receiveLoop() {{
        byte[] buffer = new byte[ProtocolConstants.MAX_MESSAGE_SIZE];

        while (!socket.isClosed()) {{
            try {{
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                socket.receive(packet);

                // Copy to frame buffer (avoid aliasing issues)
                byte[] frame = new byte[packet.getLength()];
                System.arraycopy(packet.getData(), 0, frame, 0, packet.getLength());

                dispatch(frame);
            }} catch (Exception e) {{
                if (!socket.isClosed()) {{
                    e.printStackTrace();
                }}
            }}
        }}
    }}

    /**
     * Dispatch incoming frame to callbacks
     *
     * @param frame Complete frame data: [MessageID][payload...]
     */
    private void dispatch(byte[] frame) {{
        if (frame == null || frame.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {{
            return;
        }}

        // Parse header
        byte idByte = frame[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID id = MessageID.fromValue(idByte);
        if (id == null) {{
            return;  // Unknown message ID
        }}

        // Extract payload
        int payloadLen = frame.length - ProtocolConstants.PAYLOAD_OFFSET;
        byte[] payload = new byte[payloadLen];
        System.arraycopy(frame, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLen);

        // Dispatch to typed callback (inherited from ProtocolCallbacks)
        DecoderRegistry.dispatch(this, id, payload);
    }}
}}

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// YourProtocol protocol = new YourProtocol("127.0.0.1", 9000);
//
// // Register callbacks for messages FROM controller
{callback_examples_str}
//
// // Send messages TO controller using explicit API
{method_examples_str}
//
// // Cleanup
// protocol.close();
"""

    return code
