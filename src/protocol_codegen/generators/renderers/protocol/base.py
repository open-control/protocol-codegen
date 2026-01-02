"""
Base Protocol Renderer.

Template method pattern for protocol template generation.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from protocol_codegen.core.message import Message


class ProtocolRendererBase:
    """
    Base class for protocol template renderers.

    Uses template method pattern - subclasses provide mixins,
    this class provides the assembly logic.

    Mixins must provide the following properties:
    - is_cpp: bool - Whether generating C++ code
    - is_java: bool - Whether generating Java code
    - default_transport_type: str - Default transport type name
    - protocol_name: str - Protocol name (e.g., "Serial8", "SysEx")
    """

    # Note: is_cpp, is_java, default_transport_type, protocol_name are provided by mixins
    # They are defined as @property in language/framing mixins, not as class variables here

    def render_file_header(self, output_path: Path) -> str: ...  # noqa: B027
    def render_transport_includes(self) -> str: ...  # noqa: B027
    def render_namespace_open(self, namespace: str) -> str: ...  # noqa: B027
    def render_namespace_close(self, namespace: str) -> str: ...  # noqa: B027
    def render_class_declaration(self, class_name: str) -> str: ...  # noqa: B027
    def render_constructor(self, class_name: str, transport_type: str) -> str: ...  # noqa: B027
    def render_send_method_signature(self) -> str: ...  # noqa: B027
    def render_send_method_body_start(self) -> str: ...  # noqa: B027
    def render_framing_constants(self) -> str: ...  # noqa: B027
    def render_frame_build(self) -> str: ...  # noqa: B027
    def render_send_method_body_end(self) -> str: ...  # noqa: B027
    def render_dispatch_method_signature(self) -> str: ...  # noqa: B027
    def render_frame_validate(self) -> str: ...  # noqa: B027
    def render_frame_parse(self) -> str: ...  # noqa: B027
    def render_private_section(self, transport_type: str) -> str: ...  # noqa: B027
    def render_class_close(self) -> str: ...  # noqa: B027

    def render(
        self,
        messages: list["Message"],
        output_path: Path,
        class_name: str = "Protocol",
        namespace: str = "Protocol",
    ) -> str:
        """
        Render complete protocol template file.

        Args:
            messages: List of message definitions
            output_path: Target file path
            class_name: Protocol class name
            namespace: C++ namespace (ignored for Java)

        Returns:
            Generated file content
        """
        parts = []

        # File header
        parts.append(self.render_file_header(output_path))
        parts.append(self.render_transport_includes())

        # Namespace (C++ only)
        parts.append(self.render_namespace_open(namespace))

        # Class
        parts.append(self.render_class_declaration(class_name))
        parts.append(self.render_constructor(class_name, self.default_transport_type))

        # Methods include (C++ only for .inl)
        if self.is_cpp:
            parts.append('\n#include "ProtocolMethods.inl"\n')

        # Send method
        parts.append(self.render_send_method_signature())
        parts.append(self.render_send_method_body_start())
        parts.append(self.render_framing_constants())
        parts.append(self.render_frame_build())
        parts.append(self.render_send_method_body_end())

        # Dispatch method
        parts.append(self._render_dispatch_method())

        # Private section
        parts.append(self.render_private_section(self.default_transport_type))

        # Close class
        parts.append(self.render_class_close())

        # Close namespace (C++ only)
        parts.append(self.render_namespace_close(namespace))

        # Usage example
        parts.append(self._render_usage_example(messages, class_name))

        return "".join(parts)

    def _render_dispatch_method(self) -> str:
        """Render complete dispatch method."""
        parts = [
            "\n",
            self.render_dispatch_method_signature(),
            " {\n",
            self.render_frame_validate(),
            self.render_frame_parse(),
            "    }\n",
        ]
        return "".join(parts)

    def _render_usage_example(
        self,
        messages: list["Message"],
        class_name: str,
    ) -> str:
        """Render usage example as comments."""
        lines = ["\n// " + "=" * 76]
        lines.append("// USAGE EXAMPLE")
        lines.append("// " + "=" * 76)
        lines.append("//")
        lines.append(f"// {class_name} protocol(...);")
        lines.append("//")
        lines.append("// // Register callbacks")

        # Show first 3 TO_CONTROLLER messages as callback examples
        count = 0
        for msg in messages:
            if msg.is_to_controller() and count < 3:
                pascal = "".join(w.capitalize() for w in msg.name.split("_"))
                lines.append(
                    f"// protocol.on{pascal} = [](const {pascal}Message& msg) {{ }};"
                )
                count += 1

        lines.append("//")
        lines.append("// // Send messages")

        # Show first 3 TO_HOST messages as send examples
        count = 0
        for msg in messages:
            if msg.is_to_host() and count < 3:
                pascal = "".join(w.capitalize() for w in msg.name.split("_"))
                lines.append(f"// protocol.send({pascal}Message{{...}});")
                count += 1

        lines.append("")
        return "\n".join(lines)


__all__ = ["ProtocolRendererBase"]
