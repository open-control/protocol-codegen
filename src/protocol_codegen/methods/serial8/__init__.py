"""
Serial8 Protocol Method

8-bit binary protocol for high-bandwidth serial communication.
Uses full 8-bit byte range (0x00-0xFF) for optimal efficiency.
"""

from .config import Serial8Config, Serial8Limits, Serial8Structure

__all__ = [
    "Serial8Config",
    "Serial8Limits",
    "Serial8Structure",
]
