"""
Protocol.java.template Generator for SysEx

Generates a template Protocol class that users should copy and customize.
The template is NOT compiled directly - users copy it to Protocol.java and
adapt it to their specific transport layer.

SysEx-specific:
- Uses MIDI SysEx (F0 ... F7)
- Header: [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][fromHost][payload...][F7]
- 7-bit encoding (all bytes < 0x80)
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
    Generate Protocol.java.template for SysEx transport.

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
        callback_examples.append(f"        // protocol.{callback_name} = msg -> {{ }};")

    callback_examples_str = "\n".join(callback_examples)

    code = f"""package {package};

/**
 * Protocol.java.template - SysEx Protocol Handler Template
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as Protocol.java (remove .template)
 * 2. Add your transport dependencies (MidiOut, MidiIn, ControllerHost, etc.)
 * 3. Implement send() and SysEx callback for your transport
 * 4. Add any project-specific helper methods
 *
 * This template is NOT compiled directly. It provides the structure and
 * imports you need to create your Protocol class.
 *
 * ============================================================================
 * SYSEX FRAMING
 * ============================================================================
 *
 * Frame format:
 *   [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][fromHost][payload...][F7]
 *
 * - F0 = SysEx Start (0xF0)
 * - F7 = SysEx End (0xF7)
 * - All bytes in payload must be < 0x80 (7-bit encoding)
 *
 * ============================================================================
 * TRANSPORT EXAMPLES
 * ============================================================================
 *
 * Bitwig Controller API:
 *   - Send via MidiOut.sendSysex()
 *   - Receive via MidiIn.setSysexCallback()
 *
 * ============================================================================
 */

import {package}.struct.*;

/**
 * SysEx Protocol Handler
 *
 * TODO: Customize this class for your transport layer.
 *
 * Extends ProtocolCallbacks which provides typed callback fields
 * for each message type (e.g., onTransportPlay, onDeviceChange, etc.)
 */
public class Protocol extends ProtocolCallbacks {{

    // ========================================================================
    // TODO: Add your transport members here
    // ========================================================================
    // Examples (Bitwig):
    //   private final MidiOut midiOut;
    //   private final ControllerHost host;
    //   private volatile boolean isActive = true;

    // ========================================================================
    // TODO: Constructor - adapt to your transport
    // ========================================================================

    /**
     * Example for Bitwig Controller API:
     *
     *   public Protocol(ControllerHost host, MidiOut midiOut, MidiIn midiIn) {{
     *       this.host = host;
     *       this.midiOut = midiOut;
     *
     *       // Register SysEx callback
     *       midiIn.setSysexCallback(hexData -> {{
     *           byte[] data = hexStringToByteArray(hexData);
     *           dispatch(data);
     *       }});
     *   }}
     *
     *   private static byte[] hexStringToByteArray(String hexString) {{
     *       int len = hexString.length();
     *       byte[] data = new byte[len / 2];
     *       for (int i = 0; i < len; i += 2) {{
     *           data[i / 2] = (byte) ((Character.digit(hexString.charAt(i), 16) << 4)
     *                                + Character.digit(hexString.charAt(i+1), 16));
     *       }}
     *       return data;
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
        // if (!isActive) return;  // Skip if deactivating

        try {{
            // Get MESSAGE_ID via reflection
            var messageIdField = message.getClass().getField("MESSAGE_ID");
            MessageID messageId = (MessageID) messageIdField.get(null);

            // Encode payload
            var encodeMethod = message.getClass().getMethod("encode");
            byte[] payload = (byte[]) encodeMethod.invoke(message);

            // Build SysEx frame
            byte[] sysex = buildSysExFrame(messageId.getValue(), payload);

            // TODO: Send via your transport
            // Example (Bitwig):
            //   midiOut.sendSysex(sysex);

        }} catch (Exception e) {{
            throw new RuntimeException("Failed to send message: " + e.getMessage(), e);
        }}
    }}

    private byte[] buildSysExFrame(byte messageId, byte[] payload) {{
        int totalSize = ProtocolConstants.MIN_MESSAGE_LENGTH + payload.length;
        byte[] sysex = new byte[totalSize];

        int offset = 0;
        sysex[offset++] = ProtocolConstants.SYSEX_START;
        sysex[offset++] = ProtocolConstants.MANUFACTURER_ID;
        sysex[offset++] = ProtocolConstants.DEVICE_ID;
        sysex[offset++] = messageId;
        sysex[offset++] = 1;  // fromHost = true (we are the host)

        System.arraycopy(payload, 0, sysex, offset, payload.length);
        offset += payload.length;

        sysex[offset] = ProtocolConstants.SYSEX_END;

        return sysex;
    }}

    // ========================================================================
    // Receive / Dispatch
    // ========================================================================

    /**
     * Dispatch incoming SysEx to appropriate callback
     *
     * Called by your transport's SysEx callback.
     *
     * @param sysex Raw SysEx data (including F0/F7)
     */
    public void dispatch(byte[] sysex) {{
        // Validate SysEx frame
        if (sysex == null || sysex.length < ProtocolConstants.MIN_MESSAGE_LENGTH) {{
            return;
        }}

        if (sysex[0] != ProtocolConstants.SYSEX_START ||
            sysex[sysex.length - 1] != ProtocolConstants.SYSEX_END) {{
            return;
        }}

        if (sysex[1] != ProtocolConstants.MANUFACTURER_ID ||
            sysex[2] != ProtocolConstants.DEVICE_ID) {{
            return;
        }}

        // Parse header
        byte messageIdByte = sysex[ProtocolConstants.MESSAGE_TYPE_OFFSET];
        MessageID messageId = MessageID.fromValue(messageIdByte);
        if (messageId == null) {{
            return;
        }}

        boolean fromHost = (sysex[ProtocolConstants.FROM_HOST_OFFSET] != 0);

        // Extract payload
        int payloadLength = sysex.length - ProtocolConstants.MIN_MESSAGE_LENGTH;
        byte[] payload = new byte[payloadLength];
        System.arraycopy(sysex, ProtocolConstants.PAYLOAD_OFFSET, payload, 0, payloadLength);

        // Dispatch to callbacks
        DecoderRegistry.dispatch(this, messageId, payload, fromHost);
    }}

    // ========================================================================
    // TODO: Add project-specific helper methods here
    // ========================================================================
    // Examples:
    //   public void deactivate() {{ isActive = false; }}
    //   public void requestHostStatus() {{ send(new RequestHostStatusMessage()); }}

}}  // class Protocol

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// Protocol protocol = new Protocol(host, midiOut, midiIn);
//
// // Register callbacks
{callback_examples_str}
//
// // Send messages
// protocol.send(new TransportPlayMessage(true));
"""

    return code
