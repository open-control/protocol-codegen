"""
Java Encoder Generator for SysEx Protocol.

Wrapper around EncoderTemplate for backward compatibility.
Uses JavaBackend + SysExEncodingStrategy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from protocol_codegen.generators.backends import JavaBackend
from protocol_codegen.generators.common.encoding import SysExEncodingStrategy
from protocol_codegen.generators.templates import EncoderTemplate

if TYPE_CHECKING:
    from pathlib import Path

    from protocol_codegen.core.loader import TypeRegistry


def generate_encoder_java(
    type_registry: TypeRegistry, output_path: Path, package: str = "protocol"
) -> str:
    """Generate Encoder.java with 7-bit SysEx encode functions for builtin types.

    Args:
        type_registry: TypeRegistry instance with loaded builtin types
        output_path: Path where Encoder.java will be written
        package: Java package name (default: 'protocol')

    Returns:
        Generated Java code as string
    """
    template = EncoderTemplate(JavaBackend(package=package), SysExEncodingStrategy())
    return template.generate(type_registry, output_path)
