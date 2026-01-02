"""
C++ Language Mixin for Protocol Renderers.

Provides C++ syntax for protocol template generation.
"""

from pathlib import Path


class CppProtocolMixin:
    """
    Mixin providing C++ syntax for protocol templates.

    Must be combined with a FramingMixin and ProtocolRendererBase.
    """

    @property
    def is_cpp(self) -> bool:
        return True

    @property
    def is_java(self) -> bool:
        return False

    @property
    def file_extension(self) -> str:
        return ".hpp"

    def render_file_header(self, output_path: Path) -> str:
        """Render C++ file header with pragma once and includes."""
        return f"""/**
 * {output_path.name} - Protocol Handler Template
 *
 * AUTO-GENERATED - Customize for your project
 */

#pragma once

#include <cstdint>
#include <cstring>

#include "MessageID.hpp"
#include "ProtocolConstants.hpp"
#include "ProtocolCallbacks.hpp"
#include "DecoderRegistry.hpp"
#include "MessageStructure.hpp"
"""

    def render_namespace_open(self, namespace: str = "Protocol") -> str:
        """Render namespace opening."""
        return f"\nnamespace {namespace} {{\n"

    def render_namespace_close(self, namespace: str = "Protocol") -> str:
        """Render namespace closing."""
        return f"\n}}  // namespace {namespace}\n"

    def render_class_declaration(self, class_name: str) -> str:
        """Render class declaration opening."""
        return f"""
class {class_name} : public ProtocolCallbacks {{
public:
"""

    def render_class_close(self) -> str:
        """Render class closing."""
        return "};\n"

    def render_constructor(self, class_name: str, transport_type: str) -> str:
        """Render constructor."""
        return f"""    explicit {class_name}({transport_type}& transport)
        : transport_(transport) {{
        transport_.setOnReceive([this](const uint8_t* data, size_t len) {{
            dispatch(data, len);
        }});
    }}

    ~{class_name}() = default;

    // Non-copyable, non-movable
    {class_name}(const {class_name}&) = delete;
    {class_name}& operator=(const {class_name}&) = delete;
    {class_name}({class_name}&&) = delete;
    {class_name}& operator=({class_name}&&) = delete;
"""

    def render_send_method_signature(self) -> str:
        """Render send method signature."""
        return "    template <typename T>\n    void send(const T& message)"

    def render_send_method_body_start(self) -> str:
        """Render start of send method body."""
        return """ {
        constexpr MessageID messageId = T::MESSAGE_ID;

        // Encode payload
        uint8_t payload[T::MAX_PAYLOAD_SIZE];
        uint16_t payloadLen = message.encode(payload, sizeof(payload));

        // Build frame
        uint8_t frame[MAX_MESSAGE_SIZE];
        uint16_t offset = 0;
"""

    def render_send_method_body_end(self) -> str:
        """Render end of send method body."""
        return """
        // Send frame
        transport_.send(frame, offset);
    }
"""

    def render_dispatch_method_signature(self) -> str:
        """Render dispatch method signature."""
        return "    void dispatch(const uint8_t* data, size_t len)"

    def render_private_section(self, transport_type: str) -> str:
        """Render private section."""
        return f"""
private:
    {transport_type}& transport_;
"""

    def render_memcpy(self, dest: str, src: str, size: str) -> str:
        """Render memcpy call."""
        return f"std::memcpy({dest}, {src}, {size});"

    def render_cast_message_id(self) -> str:
        """Render message ID cast."""
        return "static_cast<uint8_t>(messageId)"


__all__ = ["CppProtocolMixin"]
