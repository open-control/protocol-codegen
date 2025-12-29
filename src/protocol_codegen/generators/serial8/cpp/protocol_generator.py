"""
Protocol.hpp.template Generator for Serial8

Generates a template Protocol class for USB Serial communication.
Uses ISerialTransport for COBS-framed serial communication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_protocol_template_hpp(messages: list[Message], output_path: Path) -> str:
    """
    Generate Protocol.hpp.template for Serial8 transport.

    Args:
        messages: List of message definitions
        output_path: Where to write Protocol.hpp.template

    Returns:
        Generated C++ template code
    """
    # Generate example callback assignments (TO_CONTROLLER messages)
    callback_examples: list[str] = []
    for message in messages[:5]:
        if message.is_to_controller():
            pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
            callback_name = f"on{pascal_name}"
            class_name = f"{pascal_name}Message"
            callback_examples.append(
                f"//     protocol.{callback_name} = [](const {class_name}& msg) {{ }};"
            )
    if not callback_examples:
        callback_examples.append("//     // Register callbacks here...")

    callback_examples_str = "\n".join(callback_examples)

    # Generate example API method calls (TO_HOST messages)
    method_examples: list[str] = []
    for message in messages[:5]:
        if message.is_to_host():
            parts = message.name.lower().split("_")
            method_name = parts[0] + "".join(word.capitalize() for word in parts[1:])
            method_examples.append(f"//     protocol.{method_name}(...);")
    if not method_examples:
        method_examples.append("//     // Call API methods here...")

    method_examples_str = "\n".join(method_examples)

    code = f"""/**
 * Protocol.hpp.template - Serial8 Protocol Handler (USB Serial)
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as YourProtocol.hpp
 * 2. Rename the class (e.g., BitwigProtocol)
 * 3. Implement constructor with ISerialTransport&
 *
 * Wire format: [MessageID][payload...]
 * Framing: COBS (handled automatically by ISerialTransport)
 *
 * ============================================================================
 * ARCHITECTURE
 * ============================================================================
 *
 * YourProtocol : ProtocolCallbacks
 *   - Callbacks: onMessageName members (inherited from ProtocolCallbacks)
 *   - API: explicit methods like transportPlay(), deviceSelect() (from ProtocolMethods.inl)
 *   - send(): private, called by API methods
 *   - dispatch(): private, called by transport on receive
 *
 * ============================================================================
 */

#pragma once

#include <cstdint>
#include <cstring>

#include <oc/hal/ISerialTransport.hpp>
#include <oc/log/Log.hpp>

#include "DecoderRegistry.hpp"
#include "MessageID.hpp"
#include "ProtocolCallbacks.hpp"
#include "ProtocolConstants.hpp"

namespace YourNamespace {{

/**
 * Serial8 Protocol Handler (USB Serial with COBS framing)
 *
 * Inherits from ProtocolCallbacks for message callbacks.
 * Include ProtocolMethods.inl for explicit API methods.
 */
class YourProtocol : public Protocol::ProtocolCallbacks {{
public:
    /**
     * Construct protocol with ISerialTransport
     *
     * The transport handles COBS framing internally.
     * When a complete frame arrives, it calls our dispatch() callback.
     *
     * @param transport Reference to ISerialTransport (must outlive Protocol)
     */
    explicit YourProtocol(oc::hal::ISerialTransport& transport)
        : transport_(transport) {{
        transport_.setOnReceive([this](const uint8_t* data, size_t len) {{
            dispatch(data, len);
        }});
    }}

    ~YourProtocol() = default;

    // Non-copyable, non-movable
    YourProtocol(const YourProtocol&) = delete;
    YourProtocol& operator=(const YourProtocol&) = delete;
    YourProtocol(YourProtocol&&) = delete;
    YourProtocol& operator=(YourProtocol&&) = delete;

    // =========================================================================
    // Explicit API Methods (generated)
    // =========================================================================
    // Examples: transportPlay(bool), deviceSelect(uint8_t), requestHostStatus()
    // These methods call send() internally.
#include "ProtocolMethods.inl"

private:
    oc::hal::ISerialTransport& transport_;

    /**
     * Send a typed message (internal - called by API methods)
     */
    template <typename T>
    void send(const T& message) {{
        using Protocol::MAX_MESSAGE_SIZE;

        constexpr Protocol::MessageID messageId = T::MESSAGE_ID;

        // Encode payload
        uint8_t payload[T::MAX_PAYLOAD_SIZE];
        uint16_t payloadLen = message.encode(payload, sizeof(payload));

        // Build frame: [MessageID][payload...]
        uint8_t frame[MAX_MESSAGE_SIZE];
        uint16_t offset = 0;

        frame[offset++] = static_cast<uint8_t>(messageId);
        std::memcpy(frame + offset, payload, payloadLen);
        offset += payloadLen;

        // Send (COBS framing handled by transport)
        transport_.send(frame, offset);
    }}

    /**
     * Dispatch incoming frame to callbacks (called by transport)
     */
    void dispatch(const uint8_t* data, size_t len) {{
        using Protocol::MIN_MESSAGE_LENGTH;
        using Protocol::MESSAGE_TYPE_OFFSET;
        using Protocol::PAYLOAD_OFFSET;
        using Protocol::MessageID;
        using Protocol::DecoderRegistry;

        if (data == nullptr || len < MIN_MESSAGE_LENGTH) {{
            OC_LOG_WARN("[Protocol] Invalid frame (null or too short: {{}})", len);
            return;
        }}

        MessageID messageId = static_cast<MessageID>(data[MESSAGE_TYPE_OFFSET]);
        uint16_t payloadLen = len - PAYLOAD_OFFSET;
        const uint8_t* payload = data + PAYLOAD_OFFSET;

        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
    }}
}};

}}  // namespace YourNamespace

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
//
// #include "YourProtocol.hpp"
// #include <oc/teensy/UsbSerial.hpp>
//
// oc::teensy::UsbSerial serial;
// YourNamespace::YourProtocol protocol(serial);
//
// void setup() {{
//     serial.init();
//
//     // Register callbacks for messages FROM host (TO_CONTROLLER)
{callback_examples_str}
// }}
//
// void loop() {{
//     serial.update();  // Polls and dispatches incoming messages
//
//     // Send messages TO host using explicit API
{method_examples_str}
// }}
"""

    return code
