"""
Generic Message class for SysEx protocol system

This module provides the Message class for defining SysEx messages across
all plugins. It is a generic, reusable component that can be used by any
plugin (Bitwig, Ableton, FL Studio, etc.).

The Message class represents a unit of communication with:
- Direction semantics (sent_by/listened_by)
- Field composition (using Field class)
- Validation rules

Single Responsibility: Represent a SysEx message definition.
Reusability: Used across all plugins, not specific to any one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .enums import Direction, Intent

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .field import FieldBase


@dataclass
class Message:
    """
    Pure data class for protocol message definitions (no side effects).

    A message represents a unit of communication between the controller
    and host. Direction and intent are explicitly defined for new messages.
    Legacy messages (direction=None) are still supported during migration.

    This class is generic and reusable across all plugins. Plugin-specific
    message definitions are created by instantiating this class in the
    plugin's message/*.py files.

    The message name is automatically derived from the variable name by
    the auto-discovery system in message/__init__.py.

    Attributes:
        description: Human-readable description
        fields: List of Field objects defining the message structure
        optimistic: Enable optimistic updates for this message (default: False)
        name: Message name (auto-injected by message/__init__.py, always set before use)
        direction: Message direction (TO_HOST or TO_CONTROLLER), None for legacy
        intent: Message intent (COMMAND, QUERY, NOTIFY, RESPONSE), None for legacy
        deprecated: If True, message is excluded from code generation
        response_to: For RESPONSE messages, links to the QUERY message name

    Example:
        >>> from protocol_codegen.core.message import Message
        >>> from protocol_codegen.core.enums import Direction, Intent
        >>>
        >>> TRANSPORT_PLAY = Message(
        ...     direction=Direction.TO_HOST,
        ...     intent=Intent.COMMAND,
        ...     description='Command to set transport play state',
        ...     fields=[transport_play]
        ... )
    """

    description: str  # Human-readable description
    fields: Sequence[FieldBase]  # Field definitions (can be PrimitiveField or CompositeField)
    optimistic: bool = False  # Enable optimistic updates (default: False)

    # Name is injected by auto-discovery (message/__init__.py)
    # Always set before messages are used, so we type it as str (not Optional[str])
    name: str = ""  # Default empty, but always overwritten by auto-discovery

    # New fields for protocol API migration (optional for backward compatibility)
    direction: Direction | None = None  # TO_HOST or TO_CONTROLLER
    intent: Intent | None = None  # COMMAND, QUERY, NOTIFY, RESPONSE
    deprecated: bool = False  # If True, excluded from code generation
    response_to: str | None = None  # For RESPONSE messages, links to QUERY name

    def __str__(self) -> str:
        """String representation for debugging and display"""
        name_str = self.name or "UNNAMED"
        return f"Message({name_str}, {len(self.fields)} fields)"

    def is_legacy(self) -> bool:
        """Check if message uses old format (no direction)."""
        return self.direction is None

    def is_to_host(self) -> bool:
        """Check if message goes Controller -> Host."""
        return self.direction == Direction.TO_HOST

    def is_to_controller(self) -> bool:
        """Check if message goes Host -> Controller."""
        return self.direction == Direction.TO_CONTROLLER

    def is_command(self) -> bool:
        """Check if message is a fire-and-forget command."""
        return self.intent == Intent.COMMAND

    def is_query(self) -> bool:
        """Check if message is a query expecting a response."""
        return self.intent == Intent.QUERY

    def is_notify(self) -> bool:
        """Check if message is a state notification."""
        return self.intent == Intent.NOTIFY

    def is_response(self) -> bool:
        """Check if message is a response to a query."""
        return self.intent == Intent.RESPONSE


def collect_messages(globals_dict: Mapping[str, object]) -> list[Message]:
    """
    Collect all Message instances from a module's globals and auto-inject names.

    This function eliminates manual duplication by automatically:
    1. Finding all Message instances in the provided globals
    2. Filtering to only SCREAMING_SNAKE_CASE names (convention for messages)
    3. Injecting the variable name as the message's name attribute

    Args:
        globals_dict: The module's globals() dictionary

    Returns:
        List of Message instances with names auto-injected, sorted by name
        for deterministic ordering.

    Example:
        In your message/__init__.py:

        >>> from .sensor import *
        >>> from .network import *
        >>> from protocol_codegen.core.message import collect_messages
        >>>
        >>> ALL_MESSAGES = collect_messages(globals())

        This replaces the manual pattern:

        >>> _message_map = {
        ...     "SENSOR_READING": SENSOR_READING,
        ...     "NETWORK_STATUS": NETWORK_STATUS,
        ... }
        >>> for name, msg in _message_map.items():
        ...     msg.name = name

    Note:
        Only variables with SCREAMING_SNAKE_CASE names (all uppercase with underscores)
        are considered as message definitions. This prevents accidentally including
        helper variables or imports.
    """
    messages: list[Message] = []

    for name, obj in globals_dict.items():
        # Only consider SCREAMING_SNAKE_CASE names (message naming convention)
        if not is_screaming_snake_case(name):
            continue

        # Check if it's a Message instance
        if isinstance(obj, Message):
            obj.name = name
            messages.append(obj)

    # Sort by name for deterministic ordering
    return sorted(messages, key=lambda m: m.name)


def is_screaming_snake_case(name: str) -> bool:
    """
    Check if a name follows SCREAMING_SNAKE_CASE convention.

    Args:
        name: Variable name to check

    Returns:
        True if name is SCREAMING_SNAKE_CASE (e.g., SENSOR_READING, TRANSPORT_PLAY)
    """
    if not name:
        return False

    # Must start with uppercase letter
    if not name[0].isupper():
        return False

    # Must contain only uppercase letters, digits, and underscores
    for char in name:
        if not (char.isupper() or char.isdigit() or char == "_"):
            return False

    # Must not be a dunder or single underscore prefix (private/special)
    return not name.startswith("_")
