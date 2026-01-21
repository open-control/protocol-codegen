"""
Protocol.hpp.template Generator for Binary

Generates a template Protocol class that users should copy and customize.
The template is NOT compiled directly - users copy it to Protocol.hpp and
adapt it to their specific transport layer.

This approach is needed because:
- Protocol depends on project-specific I/O (MidiAPI, Serial, TCP, etc.)
- Different projects have different lifecycle requirements
- Helper methods are project-specific
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_protocol_template_hpp(messages: list[Message], output_path: Path) -> str:
    """
    Generate Protocol.hpp.template for Binary transport.

    Args:
        messages: List of message definitions
        output_path: Where to write Protocol.hpp.template

    Returns:
        Generated C++ template code with TODO comments
    """
    # Generate example callback assignments
    callback_examples: list[str] = []
    for message in messages[:3]:  # Show first 3 as examples
        pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
        callback_name = f"on{pascal_name}"
        class_name = f"{pascal_name}Message"
        callback_examples.append(
            f"    // protocol.{callback_name} = [](const {class_name}& msg) {{ }};"
        )

    callback_examples_str = "\n".join(callback_examples)

    code = f"""/**
 * Protocol.hpp.template - Binary Protocol Handler Template
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as Protocol.hpp (remove .template)
 * 2. Replace YOUR_TRANSPORT_TYPE with your actual transport
 * 3. Implement send() and dispatch() for your transport
 * 4. Add any project-specific helper methods
 *
 * This template is NOT compiled directly. It provides the structure and
 * includes you need to create your Protocol class.
 *
 * ============================================================================
 * TRANSPORT EXAMPLES
 * ============================================================================
 *
 * Binary over USB Serial (Teensy):
 *   - Transport: oc::interface::ITransport& (UsbSerial)
 *   - Framing: COBS (handled by transport)
 *   - Header: [MessageID][fromHost][payload...]
 *
 * Binary over TCP Socket:
 *   - Transport: TcpSocket& or similar
 *   - Framing: Length-prefix or COBS
 *   - Header: [MessageID][fromHost][payload...]
 *
 * SysEx over MIDI:
 *   - Transport: oc::api::MidiAPI& + EventBus
 *   - Framing: F0 ... F7
 *   - Header: [F0][MFR][DEV][MessageID][fromHost][payload...][F7]
 *
 * ============================================================================
 */

#pragma once

// ============================================================================
// Required Includes (DO NOT REMOVE)
// ============================================================================

#include "MessageID.hpp"
#include "ProtocolConstants.hpp"
#include "ProtocolCallbacks.hpp"
#include "DecoderRegistry.hpp"
#include "MessageStructure.hpp"  // All message types

#include <cstdint>
#include <cstring>

// ============================================================================
// TODO: Add your transport include here
// ============================================================================
// Examples:
//   #include <oc/interface/ITransport.hpp>  // For Binary over USB
//   #include <oc/api/MidiAPI.hpp>           // For SysEx over MIDI
//   #include "TcpSocket.hpp"                // For TCP socket

namespace Protocol {{

/**
 * Binary Protocol Handler
 *
 * TODO: Customize this class for your transport layer.
 *
 * Inherits from ProtocolCallbacks which provides typed callback members
 * for each message type (e.g., onSensorReading, onLog, etc.)
 */
class Protocol : public ProtocolCallbacks {{
public:
    // ========================================================================
    // TODO: Constructor - adapt to your transport
    // ========================================================================

    /**
     * Example for IFrameTransport:
     *
     *   explicit Protocol(oc::interface::ITransport& transport)
     *       : transport_(transport)
     *   {{
     *       transport_.setOnReceive([this](const uint8_t* data, size_t len) {{
     *           dispatch(data, len);
     *       }});
     *   }}
     *
     * Example for MidiAPI + EventBus:
     *
     *   Protocol(oc::api::MidiAPI& midi, oc::core::event::IEventBus& events)
     *       : midi_(midi), events_(events)
     *   {{
     *       subscriptionId_ = events_.on(EventCategory::MIDI, MidiEvent::SYSEX,
     *           [this](const Event& evt) {{
     *               const auto& sysex = static_cast<const SysExEvent&>(evt);
     *               dispatch(sysex.data, sysex.length);
     *           }});
     *   }}
     */

    // Non-copyable
    Protocol(const Protocol&) = delete;
    Protocol& operator=(const Protocol&) = delete;

    // ========================================================================
    // Send API
    // ========================================================================

    /**
     * Send a typed message
     *
     * TODO: Implement for your transport.
     *
     * @tparam T Message type (has MESSAGE_ID and encode())
     * @param message Message to send
     */
    template<typename T>
    void send(const T& message) {{
        // Build frame: [MessageID][fromHost][payload...]
        uint8_t frame[ProtocolConstants::MAX_MESSAGE_SIZE];
        size_t offset = 0;

        // Header
        frame[offset++] = static_cast<uint8_t>(T::MESSAGE_ID);
        frame[offset++] = 0x00;  // fromHost = false (we are the controller)

        // Payload
        uint8_t payload[T::MAX_PAYLOAD_SIZE];
        size_t payloadLen = message.encode(payload);
        std::memcpy(frame + offset, payload, payloadLen);
        offset += payloadLen;

        // TODO: Send via your transport
        // Examples:
        //   transport_.send(frame, offset);           // IFrameTransport
        //   midi_.sendSysEx(buildSysEx(frame, offset)); // MidiAPI
        //   socket_.write(frame, offset);             // TCP
    }}

    // ========================================================================
    // Receive / Dispatch
    // ========================================================================

    /**
     * Dispatch incoming frame to appropriate callback
     *
     * Called by your transport's receive callback.
     *
     * @param data Frame data (after transport-specific decoding)
     * @param len Frame length
     */
    void dispatch(const uint8_t* data, size_t len) {{
        if (len < ProtocolConstants::MIN_MESSAGE_LENGTH) {{
            return;  // Frame too short
        }}

        // Parse header
        auto messageId = static_cast<MessageID>(data[ProtocolConstants::MESSAGE_TYPE_OFFSET]);
        bool fromHost = data[ProtocolConstants::FROM_HOST_OFFSET] != 0;

        // Extract payload
        const uint8_t* payload = data + ProtocolConstants::PAYLOAD_OFFSET;
        size_t payloadLen = len - ProtocolConstants::PAYLOAD_OFFSET;

        // Dispatch to typed callback (inherited from ProtocolCallbacks)
        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen, fromHost);
    }}

    // ========================================================================
    // TODO: Add project-specific helper methods here
    // ========================================================================
    // Examples:
    //   void requestHostStatus();
    //   void selectDevice(uint8_t index);
    //   void sendParameterValue(uint8_t index, float value);

private:
    // ========================================================================
    // TODO: Add your transport member(s) here
    // ========================================================================
    // Examples:
    //   oc::interface::ITransport& transport_;
    //   oc::api::MidiAPI& midi_;
    //   oc::core::event::IEventBus& events_;
    //   oc::core::event::SubscriptionID subscriptionId_{{0}};
}};

}}  // namespace Protocol

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// #include "Protocol.hpp"
// #include <oc/teensy/UsbSerial.hpp>
//
// oc::teensy::UsbSerial serial;
// Protocol::Protocol protocol(serial);
//
// void setup() {{
//     serial.init();
//
//     // Register callbacks
{callback_examples_str}
// }}
//
// void loop() {{
//     serial.update();  // Polls and dispatches incoming messages
//
//     // Send messages
//     // protocol.send(SensorReadingMessage{{...}});
// }}
"""

    return code
