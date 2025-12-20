"""
Protocol.java.template Generator for Serial8

Generates a template Protocol class that users should copy and customize.
The template is NOT compiled directly - users copy it to Protocol.java and
adapt it to their specific transport layer.

Serial8-specific:
- Uses TCP socket or similar for communication
- Length-prefix framing (handled by transport/bridge)
- 8-bit binary encoding
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
        Generated Java template code with TODO comments
    """
    # Generate example callback assignments
    callback_examples: list[str] = []
    for message in messages[:3]:  # Show first 3 as examples
        pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
        callback_name = f"on{pascal_name}"
        class_name = f"{pascal_name}Message"
        callback_examples.append(
            f"        // protocol.{callback_name} = msg -> {{ }};"
        )

    callback_examples_str = "\n".join(callback_examples)

    code = f"""package {package};

/**
 * Protocol.java.template - Serial8 Protocol Handler Template
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as Protocol.java (remove .template)
 * 2. Add your transport dependencies (Socket, InputStream, etc.)
 * 3. Implement send() and the receive loop for your transport
 * 4. Add any project-specific helper methods
 *
 * This template is NOT compiled directly. It provides the structure and
 * imports you need to create your Protocol class.
 *
 * ============================================================================
 * SERIAL8 FRAMING
 * ============================================================================
 *
 * Frame format (over TCP via bridge):
 *   [4-byte length (big-endian)][MessageID][fromHost][payload...]
 *
 * The bridge handles COBS framing on the serial side.
 * TCP side uses simple length-prefix framing.
 *
 * ============================================================================
 */

import {package}.struct.*;
import java.io.*;
import java.net.*;

/**
 * Serial8 Protocol Handler
 *
 * TODO: Customize this class for your transport layer.
 *
 * Extends ProtocolCallbacks which provides typed callback fields
 * for each message type (e.g., onSensorReading, onLog, etc.)
 */
public class Protocol extends ProtocolCallbacks {{

    // ========================================================================
    // TODO: Add your transport members here
    // ========================================================================
    // Examples:
    //   private final Socket socket;
    //   private final DataInputStream input;
    //   private final DataOutputStream output;
    //   private volatile boolean running = true;

    // ========================================================================
    // TODO: Constructor - adapt to your transport
    // ========================================================================

    /**
     * Example for TCP socket:
     *
     *   public Protocol(String host, int port) throws IOException {{
     *       this.socket = new Socket(host, port);
     *       this.input = new DataInputStream(socket.getInputStream());
     *       this.output = new DataOutputStream(socket.getOutputStream());
     *       startReceiveThread();
     *   }}
     *
     *   private void startReceiveThread() {{
     *       new Thread(() -> {{
     *           while (running) {{
     *               try {{
     *                   int length = input.readInt();
     *                   byte[] data = new byte[length];
     *                   input.readFully(data);
     *                   dispatch(data);
     *               }} catch (IOException e) {{
     *                   if (running) e.printStackTrace();
     *               }}
     *           }}
     *       }}).start();
     *   }}
     */

    // ========================================================================
    // Send API
    // ========================================================================

    /**
     * Send a typed message
     *
     * TODO: Implement for your transport.
     *
     * @param message Message to send (must have MESSAGE_ID and encode())
     */
    public <T> void send(T message) {{
        try {{
            // Get MESSAGE_ID via reflection
            var messageIdField = message.getClass().getField("MESSAGE_ID");
            MessageID messageId = (MessageID) messageIdField.get(null);

            // Encode payload
            var encodeMethod = message.getClass().getMethod("encode");
            byte[] payload = (byte[]) encodeMethod.invoke(message);

            // Build frame: [MessageID][fromHost][payload...]
            byte[] frame = new byte[2 + payload.length];
            frame[0] = messageId.getValue();
            frame[1] = 1;  // fromHost = true (we are the host)
            System.arraycopy(payload, 0, frame, 2, payload.length);

            // TODO: Send via your transport
            // Example:
            //   synchronized (output) {{
            //       output.writeInt(frame.length);
            //       output.write(frame);
            //       output.flush();
            //   }}

        }} catch (Exception e) {{
            throw new RuntimeException("Failed to send message: " + e.getMessage(), e);
        }}
    }}

    // ========================================================================
    // Receive / Dispatch
    // ========================================================================

    /**
     * Dispatch incoming frame to appropriate callback
     *
     * Called by your transport's receive loop.
     *
     * @param data Frame data (after length-prefix removed)
     */
    public void dispatch(byte[] data) {{
        if (data == null || data.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {{
            return;
        }}

        // Parse header
        byte messageIdByte = data[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(messageIdByte);
        if (messageId == null) {{
            return;
        }}

        boolean fromHost = (data[ProtocolConstants.FROM_HOST_OFFSET] != 0);

        // Extract payload
        int payloadLength = data.length - ProtocolConstants.PAYLOAD_OFFSET;
        byte[] payload = new byte[payloadLength];
        System.arraycopy(data, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLength);

        // Dispatch to callbacks
        DecoderRegistry.dispatch(this, messageId, payload, fromHost);
    }}

    // ========================================================================
    // TODO: Add project-specific helper methods here
    // ========================================================================
    // Examples:
    //   public void close() {{ running = false; socket.close(); }}
    //   public boolean isConnected() {{ return socket.isConnected(); }}

}}  // class Protocol

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// Protocol protocol = new Protocol("127.0.0.1", 9000);
//
// // Register callbacks
{callback_examples_str}
//
// // Send messages
// protocol.send(new SensorReadingMessage(...));
//
// // Cleanup
// protocol.close();
"""

    return code
