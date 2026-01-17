"""
Binary Protocol Method

8-bit binary protocol for high-bandwidth serial communication.
Uses full 8-bit byte range (0x00-0xFF) for optimal efficiency.
"""

from .config import BinaryConfig, BinaryLimits, BinaryStructure

__all__ = [
    "BinaryConfig",
    "BinaryLimits",
    "BinaryStructure",
]
