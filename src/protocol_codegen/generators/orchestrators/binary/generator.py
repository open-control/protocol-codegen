"""
Binary Protocol Generator

Generator for Binary (8-bit binary) protocol code generation.
Extends BaseProtocolGenerator with Binary-specific behavior.
"""

from __future__ import annotations

from pathlib import Path

from protocol_codegen.generators.languages.cpp.file_generators.constants import (
    ProtocolConfig as CppProtocolConfig,
)
from protocol_codegen.generators.languages.java.file_generators.constants import (
    ProtocolConfig as JavaProtocolConfig,
)
from protocol_codegen.generators.orchestrators.base import BaseProtocolGenerator
from protocol_codegen.generators.orchestrators.protocol_components import ProtocolComponents
from protocol_codegen.generators.orchestrators.binary.components import BinaryComponents
from protocol_codegen.generators.orchestrators.binary.config import BinaryConfig


class BinaryGenerator(BaseProtocolGenerator[BinaryConfig]):
    """
    Binary protocol generator.

    Generates C++ and Java code for 8-bit binary protocol.
    No SysEx framing, COBS handled at bridge layer.
    """

    @property
    def protocol_name(self) -> str:
        return "Binary"

    def get_components(self) -> ProtocolComponents:
        """Return Binary-specific components."""
        return BinaryComponents()

    def _log_config_info(self) -> None:
        """Log Binary-specific configuration info."""
        if self.protocol_config:
            self._log(f"  ✓ Max payload size: {self.protocol_config.limits.max_payload_size}")

    def _validate_protocol_specific(self) -> list[str]:
        """Binary has no additional validation constraints."""
        return []

    def _convert_config_to_cpp(self) -> CppProtocolConfig:
        """Convert Pydantic BinaryConfig to TypedDict for C++ generators."""
        if self.protocol_config is None:
            raise RuntimeError("Protocol config not loaded")
        return CppProtocolConfig(
            structure={
                "message_type_offset": self.protocol_config.structure.message_type_offset,
                "payload_offset": self.protocol_config.structure.payload_offset,
            },
            limits={
                "string_max_length": self.protocol_config.limits.string_max_length,
                "array_max_items": self.protocol_config.limits.array_max_items,
                "max_payload_size": self.protocol_config.limits.max_payload_size,
                "max_message_size": self.protocol_config.limits.max_message_size,
            },
        )

    def _convert_config_to_java(self) -> JavaProtocolConfig:
        """Convert Pydantic BinaryConfig to TypedDict for Java generators."""
        if self.protocol_config is None:
            raise RuntimeError("Protocol config not loaded")
        return JavaProtocolConfig(
            structure={
                "message_type_offset": self.protocol_config.structure.message_type_offset,
                "payload_offset": self.protocol_config.structure.payload_offset,
            },
            limits={
                "string_max_length": self.protocol_config.limits.string_max_length,
                "array_max_items": self.protocol_config.limits.array_max_items,
                "max_payload_size": self.protocol_config.limits.max_payload_size,
                "max_message_size": self.protocol_config.limits.max_message_size,
            },
        )


def generate_binary_protocol(
    messages_dir: Path,
    config_path: Path,
    plugin_paths_path: Path,
    output_base: Path,
    verbose: bool = False,
) -> None:
    """
    Generate Binary protocol code from message definitions.

    This is the public API for Binary generation.

    Args:
        messages_dir: Directory containing message definitions
        config_path: Path to protocol_config.py
        plugin_paths_path: Path to plugin_paths.py
        output_base: Base output directory
        verbose: Enable verbose output
    """
    generator = BinaryGenerator(verbose=verbose)
    generator.generate(messages_dir, config_path, plugin_paths_path, output_base)
