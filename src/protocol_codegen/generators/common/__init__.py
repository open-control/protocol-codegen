"""
Common utilities for code generators.

Subpackages:
- encoding: Protocol encoding strategies (Serial8, SysEx)
- cpp: C++ generation utilities
- java: Java generation utilities

NOTE: type_encoders, type_decoders, config, naming, and payload
have been moved to generators.core/
"""

# Submodules still in common/
from protocol_codegen.generators.common import cpp, encoding, java

__all__ = [
    # Subpackages
    "cpp",
    "encoding",
    "java",
]
