"""
SysEx Protocol Generator

Generator for SysEx (7-bit MIDI) protocol code generation.
Extends BaseProtocolGenerator with SysEx-specific behavior.
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
from protocol_codegen.methods.sysex.components import SysExComponents
from protocol_codegen.methods.sysex.config import SysExConfig


class SysExGenerator(BaseProtocolGenerator[SysExConfig]):
    """
    SysEx protocol generator.

    Generates C++ and Java code for 7-bit MIDI SysEx protocol.
    Includes MIDI framing (F0...F7) and 7-bit encoding.
    """

    @property
    def protocol_name(self) -> str:
        return "SysEx"

    def get_components(self) -> ProtocolComponents:
        """Return SysEx-specific components."""
        return SysExComponents()

    def _log_config_info(self) -> None:
        """Log SysEx-specific configuration info."""
        if self.protocol_config:
            self._log(
                f"  ✓ Manufacturer ID: 0x{self.protocol_config.framing.manufacturer_id:02X}"
            )
            self._log(f"  ✓ Device ID: 0x{self.protocol_config.framing.device_id:02X}")

    def _validate_protocol_specific(self) -> list[str]:
        """Validate that all enum values are ≤127 for 7-bit SysEx protocol."""
        errors: list[str] = []
        max_value = 127  # 7-bit max

        for enum_def in self.enum_defs:
            for value_name, value in enum_def.values.items():
                if value > max_value:
                    errors.append(
                        f"Enum '{enum_def.name}.{value_name}' has value {value} "
                        f"which exceeds SysEx 7-bit limit ({max_value})"
                    )

        if not errors and self.enum_defs:
            self._log(f"  ✓ Enum validation passed ({len(self.enum_defs)} enum(s), all values ≤127)")

        return errors

    def _convert_config_to_cpp(self) -> CppProtocolConfig:
        """Convert Pydantic SysExConfig to TypedDict for C++ generators."""
        if self.protocol_config is None:
            raise RuntimeError("Protocol config not loaded")
        return CppProtocolConfig(
            sysex={
                "start": self.protocol_config.framing.start,
                "end": self.protocol_config.framing.end,
                "manufacturer_id": self.protocol_config.framing.manufacturer_id,
                "device_id": self.protocol_config.framing.device_id,
                "min_message_length": self.protocol_config.structure.min_message_length,
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
        """Convert Pydantic SysExConfig to TypedDict for Java generators."""
        if self.protocol_config is None:
            raise RuntimeError("Protocol config not loaded")
        return JavaProtocolConfig(
            sysex={
                "start": self.protocol_config.framing.start,
                "end": self.protocol_config.framing.end,
                "manufacturer_id": self.protocol_config.framing.manufacturer_id,
                "device_id": self.protocol_config.framing.device_id,
                "min_message_length": self.protocol_config.structure.min_message_length,
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


def generate_sysex_protocol(
    messages_dir: Path,
    config_path: Path,
    plugin_paths_path: Path,
    output_base: Path,
    verbose: bool = False,
) -> None:
    """
    Generate SysEx protocol code from message definitions.

    This is the public API for SysEx generation.

    Args:
        messages_dir: Directory containing message definitions
        config_path: Path to protocol_config.py
        plugin_paths_path: Path to plugin_paths.py
        output_base: Base output directory
        verbose: Enable verbose output
    """
    generator = SysExGenerator(verbose=verbose)
    generator.generate(messages_dir, config_path, plugin_paths_path, output_base)
