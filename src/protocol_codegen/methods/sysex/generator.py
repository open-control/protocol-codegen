"""
SysEx Protocol Generator

Generator for SysEx (7-bit MIDI) protocol code generation.
Extends BaseProtocolGenerator with SysEx-specific behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from protocol_codegen.core.file_utils import GenerationStats, write_if_changed
from protocol_codegen.generators.backends import CppBackend, JavaBackend
from protocol_codegen.generators.common.encoding import SysExEncodingStrategy
from protocol_codegen.generators.sysex.cpp import (
    generate_constants_hpp,
    generate_decoder_registry_hpp,
    generate_enum_hpp,
    generate_message_structure_hpp,
    generate_messageid_hpp,
    generate_protocol_callbacks_hpp,
    generate_protocol_methods_hpp,
    generate_protocol_template_hpp,
    generate_struct_hpp,
)
from protocol_codegen.generators.sysex.cpp.constants_generator import (
    ProtocolConfig as CppProtocolConfig,
)
from protocol_codegen.generators.sysex.java import (
    generate_constants_java,
    generate_decoder_registry_java,
    generate_enum_java,
    generate_messageid_java,
    generate_protocol_callbacks_java,
    generate_protocol_methods_java,
    generate_protocol_template_java,
    generate_struct_java,
)
from protocol_codegen.generators.sysex.java.constants_generator import (
    ProtocolConfig as JavaProtocolConfig,
)
from protocol_codegen.generators.templates import DecoderTemplate, EncoderTemplate
from protocol_codegen.methods.base_generator import BaseProtocolGenerator
from protocol_codegen.methods.sysex.config import SysExConfig

if TYPE_CHECKING:
    pass


class SysExGenerator(BaseProtocolGenerator[SysExConfig]):
    """
    SysEx protocol generator.

    Generates C++ and Java code for 7-bit MIDI SysEx protocol.
    Includes MIDI framing (F0...F7) and 7-bit encoding.
    """

    @property
    def protocol_name(self) -> str:
        return "SysEx"

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

    def _generate_cpp(self, output_base: Path) -> None:
        """Generate all C++ files for SysEx protocol."""
        if self.registry is None or self.plugin_paths is None or self.protocol_config is None:
            raise RuntimeError("Generator not properly initialized")

        stats = GenerationStats()

        cpp_base = output_base / self.plugin_paths["output_cpp"]["base_path"]
        cpp_base.mkdir(parents=True, exist_ok=True)

        protocol_config_dict = self._convert_config_to_cpp()

        # Generate base files using templates
        cpp_backend = CppBackend()
        strategy = SysExEncodingStrategy()

        cpp_encoder_path = cpp_base / "Encoder.hpp"
        encoder_template = EncoderTemplate(cpp_backend, strategy)
        was_written = write_if_changed(
            cpp_encoder_path, encoder_template.generate(self.registry, cpp_encoder_path)
        )
        stats.record_write(cpp_encoder_path, was_written)

        cpp_decoder_path = cpp_base / "Decoder.hpp"
        decoder_template = DecoderTemplate(cpp_backend, strategy)
        was_written = write_if_changed(
            cpp_decoder_path, decoder_template.generate(self.registry, cpp_decoder_path)
        )
        stats.record_write(cpp_decoder_path, was_written)

        cpp_constants_path = cpp_base / "ProtocolConstants.hpp"
        was_written = write_if_changed(
            cpp_constants_path,
            generate_constants_hpp(protocol_config_dict, self.registry, cpp_constants_path),
        )
        stats.record_write(cpp_constants_path, was_written)

        cpp_messageid_path = cpp_base / "MessageID.hpp"
        was_written = write_if_changed(
            cpp_messageid_path,
            generate_messageid_hpp(
                self.messages, self.allocations, self.registry, cpp_messageid_path
            ),
        )
        stats.record_write(cpp_messageid_path, was_written)

        cpp_message_structure_path = cpp_base / "MessageStructure.hpp"
        was_written = write_if_changed(
            cpp_message_structure_path,
            generate_message_structure_hpp(self.messages, cpp_message_structure_path),
        )
        stats.record_write(cpp_message_structure_path, was_written)

        cpp_callbacks_path = cpp_base / "ProtocolCallbacks.hpp"
        was_written = write_if_changed(
            cpp_callbacks_path,
            generate_protocol_callbacks_hpp(self.messages, cpp_callbacks_path),
        )
        stats.record_write(cpp_callbacks_path, was_written)

        cpp_decoder_registry_path = cpp_base / "DecoderRegistry.hpp"
        was_written = write_if_changed(
            cpp_decoder_registry_path,
            generate_decoder_registry_hpp(self.messages, cpp_decoder_registry_path),
        )
        stats.record_write(cpp_decoder_registry_path, was_written)

        cpp_protocol_template_path = cpp_base / "Protocol.hpp.template"
        was_written = write_if_changed(
            cpp_protocol_template_path,
            generate_protocol_template_hpp(self.messages, cpp_protocol_template_path),
        )
        stats.record_write(cpp_protocol_template_path, was_written)

        # Generate enum files
        enum_stats = GenerationStats()
        for enum_def in self.enum_defs:
            cpp_enum_path = cpp_base / f"{enum_def.name}.hpp"
            cpp_enum_code = generate_enum_hpp(enum_def, cpp_enum_path)
            was_written = write_if_changed(cpp_enum_path, cpp_enum_code)
            enum_stats.record_write(cpp_enum_path, was_written)

        # Generate ProtocolMethods.inl for new-style messages
        new_style_messages = [m for m in self.messages if not m.is_legacy()]
        methods_stats = GenerationStats()
        if new_style_messages:
            cpp_methods_path = cpp_base / "ProtocolMethods.inl"
            cpp_methods_code = generate_protocol_methods_hpp(new_style_messages, cpp_methods_path)
            was_written = write_if_changed(cpp_methods_path, cpp_methods_code)
            methods_stats.record_write(cpp_methods_path, was_written)

        # Generate struct files
        cpp_struct_dir = cpp_base / self.plugin_paths["output_cpp"]["structs"]
        cpp_struct_dir.mkdir(parents=True, exist_ok=True)

        struct_stats = GenerationStats()
        for message in self.messages:
            pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
            struct_name = f"{pascal_name}Message"
            cpp_output_path = cpp_struct_dir / f"{struct_name}.hpp"
            message_id = self.allocations[message.name]

            cpp_code = generate_struct_hpp(
                message,
                message_id,
                self.registry,
                cpp_output_path,
                self.protocol_config.limits.string_max_length,
                self.protocol_config.limits.include_message_name,
            )
            was_written = write_if_changed(cpp_output_path, cpp_code)
            struct_stats.record_write(cpp_output_path, was_written)

        if self.verbose:
            print(f"  ✓ C++ base files: {stats.summary()}")
            if self.enum_defs:
                print(f"  ✓ C++ enum files: {enum_stats.summary()}")
            if new_style_messages:
                print(f"  ✓ C++ ProtocolMethods.inl: {methods_stats.summary()}")
            print(f"  ✓ C++ struct files: {struct_stats.summary()}")
            print(f"  → Output: {cpp_base.relative_to(output_base)}")

    def _generate_java(self, output_base: Path) -> None:
        """Generate all Java files for SysEx protocol."""
        if self.registry is None or self.plugin_paths is None or self.protocol_config is None:
            raise RuntimeError("Generator not properly initialized")

        stats = GenerationStats()

        java_base = output_base / self.plugin_paths["output_java"]["base_path"]
        java_base.mkdir(parents=True, exist_ok=True)

        java_package = self.plugin_paths["output_java"]["package"]
        struct_package = f"{java_package}.struct"
        protocol_config_dict = self._convert_config_to_java()

        # Generate base files using templates
        java_backend = JavaBackend(package=java_package)
        strategy = SysExEncodingStrategy()

        java_encoder_path = java_base / "Encoder.java"
        encoder_template = EncoderTemplate(java_backend, strategy)
        was_written = write_if_changed(
            java_encoder_path,
            encoder_template.generate(self.registry, java_encoder_path),
        )
        stats.record_write(java_encoder_path, was_written)

        java_decoder_path = java_base / "Decoder.java"
        decoder_template = DecoderTemplate(java_backend, strategy)
        was_written = write_if_changed(
            java_decoder_path,
            decoder_template.generate(self.registry, java_decoder_path),
        )
        stats.record_write(java_decoder_path, was_written)

        java_constants_path = java_base / "ProtocolConstants.java"
        was_written = write_if_changed(
            java_constants_path,
            generate_constants_java(protocol_config_dict, java_constants_path, java_package),
        )
        stats.record_write(java_constants_path, was_written)

        java_messageid_path = java_base / "MessageID.java"
        was_written = write_if_changed(
            java_messageid_path,
            generate_messageid_java(
                self.messages,
                self.allocations,
                self.registry,
                java_messageid_path,
                java_package,
            ),
        )
        stats.record_write(java_messageid_path, was_written)

        java_callbacks_path = java_base / "ProtocolCallbacks.java"
        was_written = write_if_changed(
            java_callbacks_path,
            generate_protocol_callbacks_java(self.messages, java_package, java_callbacks_path),
        )
        stats.record_write(java_callbacks_path, was_written)

        java_decoder_registry_path = java_base / "DecoderRegistry.java"
        was_written = write_if_changed(
            java_decoder_registry_path,
            generate_decoder_registry_java(
                self.messages, java_package, java_decoder_registry_path
            ),
        )
        stats.record_write(java_decoder_registry_path, was_written)

        java_protocol_template_path = java_base / "Protocol.java.template"
        was_written = write_if_changed(
            java_protocol_template_path,
            generate_protocol_template_java(
                self.messages, java_protocol_template_path, java_package
            ),
        )
        stats.record_write(java_protocol_template_path, was_written)

        # Generate enum files
        enum_stats = GenerationStats()
        for enum_def in self.enum_defs:
            java_enum_path = java_base / f"{enum_def.name}.java"
            java_enum_code = generate_enum_java(enum_def, java_enum_path)
            was_written = write_if_changed(java_enum_path, java_enum_code)
            enum_stats.record_write(java_enum_path, was_written)

        # Generate ProtocolMethods.java for new-style messages
        new_style_messages = [m for m in self.messages if not m.is_legacy()]
        methods_stats = GenerationStats()
        if new_style_messages:
            java_methods_path = java_base / "ProtocolMethods.java"
            java_methods_code = generate_protocol_methods_java(
                new_style_messages, java_methods_path, java_package, self.registry
            )
            was_written = write_if_changed(java_methods_path, java_methods_code)
            methods_stats.record_write(java_methods_path, was_written)

        # Generate struct files
        java_struct_dir = java_base / self.plugin_paths["output_java"]["structs"]
        java_struct_dir.mkdir(parents=True, exist_ok=True)

        struct_stats = GenerationStats()
        for message in self.messages:
            pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
            class_name = f"{pascal_name}Message"
            java_output_path = java_struct_dir / f"{class_name}.java"
            message_id = self.allocations[message.name]

            java_code = generate_struct_java(
                message,
                message_id,
                self.registry,
                java_output_path,
                self.protocol_config.limits.string_max_length,
                struct_package,
                self.protocol_config.limits.include_message_name,
            )
            was_written = write_if_changed(java_output_path, java_code)
            struct_stats.record_write(java_output_path, was_written)

        if self.verbose:
            print(f"  ✓ Java base files: {stats.summary()}")
            if self.enum_defs:
                print(f"  ✓ Java enum files: {enum_stats.summary()}")
            if new_style_messages:
                print(f"  ✓ Java ProtocolMethods.java: {methods_stats.summary()}")
            print(f"  ✓ Java struct files: {struct_stats.summary()}")
            print(f"  → Output: {java_base.relative_to(output_base)}")


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
