"""
ProtocolCallbacks.java Generator

Generates base class with typed callbacks for each message.
Protocol extends this and users assign callbacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.common.naming import (
    message_name_to_callback_name,
    to_pascal_case,
)

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.message import Message


def generate_protocol_callbacks_java(
    messages: list[Message], package: str, output_path: Path
) -> str:
    """
    Generate ProtocolCallbacks.java.

    Args:
        messages: List of message definitions
        package: Base package name (e.g., "com.midi_studio")
        output_path: Where to write ProtocolCallbacks.java

    Returns:
        Generated Java code
    """
    # Generate callback declarations for each message
    callbacks: list[str] = []
    for message in messages:
        class_name = f"{to_pascal_case(message.name)}Message"
        callback_name = message_name_to_callback_name(message.name)

        callbacks.append(f"    public MessageHandler<{class_name}> {callback_name};")

    callbacks_str = "\n".join(callbacks)

    code = f"""package {package};

import {package}.struct.*;

/**
 * ProtocolCallbacks - Typed callbacks for all messages
 *
 * AUTO-GENERATED - DO NOT EDIT
 *
 * Base class providing typed callbacks for each message type.
 * Extends ProtocolMethods for explicit send API.
 * Protocol extends this and DecoderRegistry calls these callbacks.
 *
 * Inheritance: ProtocolMethods -> ProtocolCallbacks -> Protocol
 *
 * Usage:
 *   protocol.onTransportPlay = msg -> {{
 *       System.out.println("Playing: " + msg.isPlaying());
 *   }};
 */
public abstract class ProtocolCallbacks extends ProtocolMethods {{

    /**
     * Functional interface for message handlers
     */
    @FunctionalInterface
    public interface MessageHandler<T> {{
        void handle(T message);
    }}

    // ========================================================================
    // Typed callbacks (one per message)
    // ========================================================================

{callbacks_str}

    protected ProtocolCallbacks() {{}}
}}
"""

    return code
