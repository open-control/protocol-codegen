"""
C++ Encoder Generator for SysEx Protocol.

Wrapper around EncoderTemplate for backward compatibility.
Uses CppBackend + SysExEncodingStrategy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.backends import CppBackend
from protocol_codegen.generators.common.encoding import SysExEncodingStrategy
from protocol_codegen.generators.templates import EncoderTemplate

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


def generate_encoder_hpp(type_registry: TypeRegistry, output_path: Path) -> str:
    """Generate Encoder.hpp with 7-bit SysEx encode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Encoder.hpp will be written

    Returns:
        Generated C++ code as string
    """
    template = EncoderTemplate(CppBackend(), SysExEncodingStrategy())
    return template.generate(type_registry, output_path)
