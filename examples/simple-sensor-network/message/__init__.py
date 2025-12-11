"""
Message definitions for simple-sensor-network example.

This module imports all message definitions and automatically collects them
using the collect_messages helper, which:
1. Finds all Message instances with SCREAMING_SNAKE_CASE names
2. Auto-injects the variable name as the message's name attribute
3. Returns a sorted list for deterministic ID allocation
"""

from protocol_codegen.core.message import collect_messages

from .network import *
from .sensor import *

# Automatically collect all Message instances and inject names
# This replaces the manual _message_map pattern
ALL_MESSAGES = collect_messages(globals())
