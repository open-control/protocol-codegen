"""
Java Language Mixin for Protocol Renderers.

Provides Java syntax for protocol template generation.
"""

from pathlib import Path


class JavaProtocolMixin:
    """
    Mixin providing Java syntax for protocol templates.

    Must be combined with a FramingMixin and ProtocolRendererBase.
    """

    def __init__(self, package: str = "protocol") -> None:
        self.package = package

    @property
    def is_cpp(self) -> bool:
        return False

    @property
    def is_java(self) -> bool:
        return True

    @property
    def file_extension(self) -> str:
        return ".java"

    def render_file_header(self, output_path: Path) -> str:
        """Render Java file header with package and imports."""
        return f"""package {self.package};

/**
 * {output_path.stem} - Protocol Handler Template
 *
 * AUTO-GENERATED - Customize for your project
 */

import {self.package}.struct.*;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
"""

    def render_namespace_open(self, namespace: str = "") -> str:
        """Java doesn't have namespaces, return empty."""
        return ""

    def render_namespace_close(self, namespace: str = "") -> str:
        """Java doesn't have namespaces, return empty."""
        return ""

    def render_class_declaration(self, class_name: str) -> str:
        """Render class declaration opening."""
        return f"""
public class {class_name} extends ProtocolCallbacks {{
"""

    def render_class_close(self) -> str:
        """Render class closing."""
        return "}  // class\n"

    def render_constructor(self, class_name: str, transport_type: str) -> str:
        """Render constructor - abstract in template."""
        return f"""    // TODO: Implement constructor with your transport
    // public {class_name}({transport_type} transport) {{ ... }}
"""

    def render_send_method_signature(self) -> str:
        """Render send method signature."""
        return "    public <T> void send(T message)"

    def render_send_method_body_start(self) -> str:
        """Render start of send method body."""
        return """ {
        if (message == null) return;

        try {
            // Get MESSAGE_ID via reflection
            Field idField = message.getClass().getField("MESSAGE_ID");
            MessageID messageId = (MessageID) idField.get(null);

            // Encode payload
            Method encodeMethod = message.getClass().getMethod("encode");
            byte[] payload = (byte[]) encodeMethod.invoke(message);

            // Build frame
            byte[] frame = new byte[ProtocolConstants.MAX_MESSAGE_SIZE];
            int offset = 0;
"""

    def render_send_method_body_end(self) -> str:
        """Render end of send method body."""
        return """
            // TODO: Send via your transport
            // transport.send(frame, 0, offset);

        } catch (Exception e) {
            throw new RuntimeException("Failed to send: " + e.getMessage(), e);
        }
    }
"""

    def render_dispatch_method_signature(self) -> str:
        """Render dispatch method signature."""
        return "    public void dispatch(byte[] data)"

    def render_private_section(self, transport_type: str) -> str:
        """Render private section."""
        return f"""
    // TODO: Add your transport member
    // private {transport_type} transport;
"""

    def render_arraycopy(
        self, src: str, src_pos: str, dest: str, dest_pos: str, length: str
    ) -> str:
        """Render System.arraycopy call."""
        return f"System.arraycopy({src}, {src_pos}, {dest}, {dest_pos}, {length});"

    def render_cast_message_id(self) -> str:
        """Render message ID cast."""
        return "messageId.getValue()"


__all__ = ["JavaProtocolMixin"]
