"""
Protocol Generation Orchestrators.

This module coordinates the full generation pipeline for each protocol type.

Available orchestrators:
- serial8: Serial8 protocol generation
- sysex: SysEx protocol generation
"""

from protocol_codegen.generators.orchestrators.base import BaseProtocolGenerator
from protocol_codegen.generators.orchestrators.common import collect_enum_defs
from protocol_codegen.generators.orchestrators.protocol_components import (
    ProtocolComponents,
)

__all__ = [
    "BaseProtocolGenerator",
    "collect_enum_defs",
    "ProtocolComponents",
]
