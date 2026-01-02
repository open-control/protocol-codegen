"""
Framing Mixins - Re-exports from generators.protocols.

NOTE: This module is deprecated. Import directly from:
- generators.protocols.serial8 (Serial8FramingMixin)
- generators.protocols.sysex (SysExFramingMixin)
"""

from protocol_codegen.generators.protocols.serial8 import Serial8FramingMixin
from protocol_codegen.generators.protocols.sysex import SysExFramingMixin

__all__ = [
    "Serial8FramingMixin",
    "SysExFramingMixin",
]
