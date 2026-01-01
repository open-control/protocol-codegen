"""
Framing Mixins for Protocol Renderers.

Each mixin provides protocol-specific framing logic.
"""

from protocol_codegen.generators.renderers.protocol.mixins.framings.serial8 import (
    Serial8FramingMixin,
)
from protocol_codegen.generators.renderers.protocol.mixins.framings.sysex import (
    SysExFramingMixin,
)

__all__ = [
    "Serial8FramingMixin",
    "SysExFramingMixin",
]
