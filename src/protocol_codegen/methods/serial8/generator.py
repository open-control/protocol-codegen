"""
Serial8 Protocol Generator

Generator for Serial8 (8-bit binary) protocol code generation.
Extends BaseProtocolGenerator with Serial8-specific behavior.
"""

from __future__ import annotations

from pathlib import Path

from protocol_codegen.generators.common.cpp.constants_generator import (
    ProtocolConfig as CppProtocolConfig,
)
from protocol_codegen.generators.common.java.constants_generator import (
    ProtocolConfig as JavaProtocolConfig,
)
from protocol_codegen.methods.base_generator import BaseProtocolGenerator
from protocol_codegen.methods.protocol_components import ProtocolComponents
from protocol_codegen.methods.serial8.components import Serial8Components
from protocol_codegen.methods.serial8.config import Serial8Config


class Serial8Generator(BaseProtocolGenerator[Serial8Config]):
    """
    Serial8 protocol generator.

    Generates C++ and Java code for 8-bit binary protocol.
    No SysEx framing, COBS handled at bridge layer.
    """

    @property
    def protocol_name(self) -> str:
        return "Serial8"

    def get_components(self) -> ProtocolComponents:
        """Return Serial8-specific components."""
        return Serial8Components()

    def _log_config_info(self) -> None:
        """Log Serial8-specific configuration info."""
        if self.protocol_config:
            self._log(f"  ✓ Max payload size: {self.protocol_config.limits.max_payload_size}")

    def _validate_protocol_specific(self) -> list[str]:
        """Serial8 has no additional validation constraints."""
        return []

    def _convert_config_to_cpp(self) -> CppProtocolConfig:
        """Convert Pydantic Serial8Config to TypedDict for C++ generators."""
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
        """Convert Pydantic Serial8Config to TypedDict for Java generators."""
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


def generate_serial8_protocol(
    messages_dir: Path,
    config_path: Path,
    plugin_paths_path: Path,
    output_base: Path,
    verbose: bool = False,
) -> None:
    """
    Generate Serial8 protocol code from message definitions.

    This is the public API for Serial8 generation.

    Args:
        messages_dir: Directory containing message definitions
        config_path: Path to protocol_config.py
        plugin_paths_path: Path to plugin_paths.py
        output_base: Base output directory
        verbose: Enable verbose output
    """
    generator = Serial8Generator(verbose=verbose)
    generator.generate(messages_dir, config_path, plugin_paths_path, output_base)
