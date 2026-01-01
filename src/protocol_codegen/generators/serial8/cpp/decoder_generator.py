"""
C++ Decoder Generator for Serial8 Protocol.

Wrapper around DecoderTemplate for backward compatibility.
Uses CppBackend + Serial8EncodingStrategy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.backends import CppBackend
from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy
from protocol_codegen.generators.templates import DecoderTemplate

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


def generate_decoder_hpp(type_registry: TypeRegistry, output_path: Path) -> str:
    """Generate Decoder.hpp with 8-bit decode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Decoder.hpp will be written

    Returns:
        Generated C++ code as string
    """
    template = DecoderTemplate(CppBackend(), Serial8EncodingStrategy())
    return template.generate(type_registry, output_path)
