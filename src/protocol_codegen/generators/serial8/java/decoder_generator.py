"""
Java Decoder Generator for Serial8 Protocol.

Wrapper around DecoderTemplate for backward compatibility.
Uses JavaBackend + Serial8EncodingStrategy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.backends import JavaBackend
from protocol_codegen.generators.common.encoding import Serial8EncodingStrategy
from protocol_codegen.generators.templates import DecoderTemplate

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


def generate_decoder_java(
    type_registry: TypeRegistry, output_path: Path, package: str = "protocol"
) -> str:
    """Generate Decoder.java with 8-bit decode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Decoder.java will be written
        package: Java package name (default: 'protocol')

    Returns:
        Generated Java code as string
    """
    template = DecoderTemplate(JavaBackend(package=package), Serial8EncodingStrategy())
    return template.generate(type_registry, output_path)
