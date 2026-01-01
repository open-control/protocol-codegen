"""
Protocol.hpp.template Generator for SysEx

Generates a template Protocol class that users should copy and customize.
The template is NOT compiled directly - users copy it to Protocol.hpp and
adapt it to their specific transport layer.

SysEx-specific framing:
- Uses MIDI SysEx (F0 ... F7)
- Header: [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][payload...][F7]
- 7-bit encoding (all bytes < 0x80)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_protocol_template_hpp(messages: list[Message], output_path: Path) -> str:
    """
    Generate Protocol.hpp.template for SysEx transport.

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
 * Protocol.hpp.template - SysEx Protocol Handler Template
 *
 * ============================================================================
 * HOW TO USE THIS TEMPLATE
 * ============================================================================
 *
 * 1. Copy this file to your project as Protocol.hpp (remove .template)
 * 2. Add your transport dependencies (MidiAPI, EventBus, etc.)
 * 3. Implement send() and dispatch() for your transport
 * 4. Add any project-specific helper methods
 *
 * This template is NOT compiled directly. It provides the structure and
 * includes you need to create your Protocol class.
 *
 * ============================================================================
 * SYSEX FRAMING
 * ============================================================================
 *
 * Frame format:
 *   [F0][MANUFACTURER_ID][DEVICE_ID][MessageID][payload...][F7]
 *
 * - F0 = SysEx Start (0xF0)
 * - F7 = SysEx End (0xF7)
 * - All bytes in payload must be < 0x80 (7-bit encoding)
 *
 * ============================================================================
 * TRANSPORT EXAMPLES
 * ============================================================================
 *
 * Using open-control framework (MidiAPI + EventBus):
 *   - Send via MidiAPI::sendSysEx()
 *   - Receive via EventBus subscription to SysExEvent
 *
 * Using Bitwig API directly:
 *   - Send via MidiOut::sendSysex()
 *   - Receive via MidiIn::setSysexCallback()
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
//   #include <oc/api/MidiAPI.hpp>           // For open-control framework
//   #include <oc/core/event/IEventBus.hpp>  // For EventBus subscription
//   #include <oc/core/event/Events.hpp>     // For SysExEvent

namespace Protocol {{

/**
 * SysEx Protocol Handler
 *
 * TODO: Customize this class for your transport layer.
 *
 * Inherits from ProtocolCallbacks which provides typed callback members
 * for each message type (e.g., onTransportPlay, onDeviceChange, etc.)
 */
class Protocol : public ProtocolCallbacks {{
public:
    // ========================================================================
    // TODO: Constructor - adapt to your transport
    // ========================================================================

    /**
     * Example for open-control framework (MidiAPI + EventBus):
     *
     *   Protocol(oc::api::MidiAPI& midi, oc::core::event::IEventBus& events)
     *       : midi_(midi), events_(events)
     *   {{
     *       using namespace oc::core::event;
     *       subscriptionId_ = events_.on(
     *           EventCategory::MIDI,
     *           MidiEvent::SYSEX,
     *           [this](const Event& evt) {{
     *               const auto& sysex = static_cast<const SysExEvent&>(evt);
     *               dispatch(sysex.data, sysex.length);
     *           }});
     *   }}
     *
     *   ~Protocol() {{
     *       events_.off(subscriptionId_);
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
        // Encode payload
        uint8_t payload[T::MAX_PAYLOAD_SIZE];
        uint16_t payloadLen = message.encode(payload, sizeof(payload));

        // Build SysEx frame
        uint8_t sysex[MAX_MESSAGE_SIZE];
        uint16_t offset = 0;

        sysex[offset++] = SYSEX_START;
        sysex[offset++] = MANUFACTURER_ID;
        sysex[offset++] = DEVICE_ID;
        sysex[offset++] = static_cast<uint8_t>(T::MESSAGE_ID);

        std::memcpy(sysex + offset, payload, payloadLen);
        offset += payloadLen;

        sysex[offset++] = SYSEX_END;

        // TODO: Send via your transport
        // Example:
        //   midi_.sendSysEx(sysex, offset);
    }}

    // ========================================================================
    // Receive / Dispatch
    // ========================================================================

    /**
     * Dispatch incoming SysEx to appropriate callback
     *
     * Called by your transport's receive callback.
     *
     * @param sysex Raw SysEx data (including F0/F7)
     * @param length SysEx length
     */
    void dispatch(const uint8_t* sysex, uint16_t length) {{
        // Validate SysEx frame
        if (sysex == nullptr || length < MIN_MESSAGE_LENGTH) {{
            return;
        }}

        if (sysex[0] != SYSEX_START || sysex[length - 1] != SYSEX_END) {{
            return;
        }}

        if (sysex[1] != MANUFACTURER_ID || sysex[2] != DEVICE_ID) {{
            return;
        }}

        // Parse header
        MessageID messageId = static_cast<MessageID>(sysex[MESSAGE_TYPE_OFFSET]);

        // Extract payload
        uint16_t payloadLen = length - MIN_MESSAGE_LENGTH;
        const uint8_t* payload = sysex + PAYLOAD_OFFSET;

        // Dispatch to typed callback
        DecoderRegistry::dispatch(*this, messageId, payload, payloadLen);
    }}

    // ========================================================================
    // TODO: Add project-specific helper methods here
    // ========================================================================
    // Examples:
    //   void requestHostStatus();
    //   void selectDevice(uint8_t index);
    //   void sendParameterValue(uint8_t index, float value);
    //   void togglePlay();

private:
    // ========================================================================
    // TODO: Add your transport member(s) here
    // ========================================================================
    // Examples:
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
// #include <oc/api/MidiAPI.hpp>
// #include <oc/core/event/IEventBus.hpp>
//
// class MyContext : public oc::context::IContext {{
//     Protocol protocol_;
//
// public:
//     MyContext(oc::api::MidiAPI& midi, oc::core::event::IEventBus& events)
//         : protocol_(midi, events)
//     {{
//         // Register callbacks
{callback_examples_str}
//     }}
//
//     void sendCommand() {{
//         protocol_.send(TransportPlayMessage{{true}});
//     }}
// }};
"""

    return code
