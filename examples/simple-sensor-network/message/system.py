"""
System messages for logging and diagnostics.
"""

from protocol_codegen.core.field import PrimitiveField, Type
from protocol_codegen.core.message import Message

# ============================================================================
# LOG MESSAGE FIELDS
# ============================================================================

log_message = PrimitiveField("message", type_name=Type.STRING)

# ============================================================================
# LOG MESSAGE
# ============================================================================

# Device → Host: Log message for debugging
LOG = Message(
    description="Log message from device for remote debugging",
    fields=[
        log_message,
    ],
)
