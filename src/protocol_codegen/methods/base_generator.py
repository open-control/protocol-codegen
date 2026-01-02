"""
Base Protocol Generator

Abstract base class providing the common generation pipeline.
Serial8Generator and SysExGenerator inherit from this.

Key Design:
- Unified _generate_cpp() and _generate_java() implementations
- Protocol-specific behavior delegated to ProtocolComponents
- Config conversion remains in subclasses (different config structures)
"""

from __future__ import annotations

import importlib
import importlib.util
import io
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from protocol_codegen.core.allocator import allocate_message_ids
from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.field import populate_type_names
from protocol_codegen.core.file_utils import GenerationStats, write_if_changed
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message
from protocol_codegen.core.plugin_types import PluginPathsConfig
from protocol_codegen.core.validator import ProtocolValidator
from protocol_codegen.generators.backends import CppBackend, JavaBackend
from protocol_codegen.generators.common.config import ProtocolConfig
from protocol_codegen.generators.common.cpp import (
    generate_constants_hpp,
    generate_decoder_registry_hpp,
    generate_enum_hpp,
    generate_message_structure_hpp,
    generate_messageid_hpp,
    generate_protocol_callbacks_hpp,
    generate_protocol_methods_hpp,
    generate_struct_hpp,
)
from protocol_codegen.generators.common.java import (
    generate_constants_java,
    generate_decoder_registry_java,
    generate_enum_java,
    generate_messageid_java,
    generate_protocol_callbacks_java,
    generate_protocol_methods_java,
    generate_struct_java,
)
from protocol_codegen.generators.common.naming import to_pascal_case
from protocol_codegen.generators.templates import DecoderTemplate, EncoderTemplate
from protocol_codegen.methods.common import collect_enum_defs
from protocol_codegen.methods.protocol_components import ProtocolComponents

if TYPE_CHECKING:
    from types import ModuleType


class BaseProtocolGenerator[ConfigT](ABC):
    """
    Abstract base class for protocol generators.

    Implements the common 7-step generation pipeline:
    1. Load type registry
    2. Load configuration
    3. Import messages
    4. Validate messages
    5. Allocate message IDs
    6. Generate C++ code
    7. Generate Java code

    Subclasses provide:
    - ProtocolComponents via get_components()
    - Config conversion via _convert_config_to_cpp/java()
    - Protocol-specific validation via _validate_protocol_specific()
    """

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.registry: TypeRegistry | None = None
        self.protocol_config: ConfigT | None = None
        self.plugin_paths: PluginPathsConfig | None = None
        self.messages: list[Message] = []
        self.allocations: dict[str, int] = {}
        self.enum_defs: list[EnumDef] = []

    def _log(self, msg: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(msg)

    # =========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =========================================================================

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Return protocol name for logging (e.g., 'Serial8', 'SysEx')."""
        ...

    @abstractmethod
    def get_components(self) -> ProtocolComponents:
        """
        Return protocol-specific components.

        Provides encoding strategy and protocol renderers.
        """
        ...

    @abstractmethod
    def _log_config_info(self) -> None:
        """Log protocol-specific configuration info after loading config."""
        ...

    @abstractmethod
    def _validate_protocol_specific(self) -> list[str]:
        """
        Perform protocol-specific validation.

        Returns:
            List of error messages (empty if valid)
        """
        ...

    @abstractmethod
    def _convert_config_to_cpp(self) -> ProtocolConfig:
        """Convert protocol config to TypedDict for C++ generators."""
        ...

    @abstractmethod
    def _convert_config_to_java(self) -> ProtocolConfig:
        """Convert protocol config to TypedDict for Java generators."""
        ...

    # =========================================================================
    # MAIN GENERATION PIPELINE
    # =========================================================================

    def generate(
        self,
        messages_dir: Path,
        config_path: Path,
        plugin_paths_path: Path,
        output_base: Path,
    ) -> None:
        """
        Execute the full generation pipeline.

        Args:
            messages_dir: Directory containing message definitions
            config_path: Path to protocol_config.py
            plugin_paths_path: Path to plugin_paths.py
            output_base: Base output directory
        """
        # Step 1: Load type registry
        self._step1_load_registry()

        # Step 2: Load configuration
        self._step2_load_config(config_path, plugin_paths_path)

        # Step 3: Import messages
        self._step3_import_messages(messages_dir)

        # Step 4: Validate messages
        self._step4_validate_messages()

        # Step 5: Allocate message IDs
        self._step5_allocate_ids()

        # Step 6: Generate C++ code
        self._log("[6/7] Generating C++ code...")
        self._generate_cpp(output_base)

        # Step 7: Generate Java code
        self._log("[7/7] Generating Java code...")
        self._generate_java(output_base)

    # =========================================================================
    # UNIFIED C++ GENERATION
    # =========================================================================

    def _generate_cpp(self, output_base: Path) -> None:
        """
        Generate all C++ files for this protocol.

        This is the unified implementation that works for all protocols.
        Protocol-specific behavior is delegated to:
        - get_components() for encoding strategy and renderers
        - _convert_config_to_cpp() for config conversion
        """
        if self.registry is None or self.plugin_paths is None or self.protocol_config is None:
            raise RuntimeError("Generator not properly initialized")

        components = self.get_components()
        strategy = components.get_encoding_strategy()

        stats = GenerationStats()

        cpp_base = output_base / self.plugin_paths["output_cpp"]["base_path"]
        cpp_base.mkdir(parents=True, exist_ok=True)

        protocol_config_dict = self._convert_config_to_cpp()

        # Generate base files using templates
        cpp_backend = CppBackend()

        # Encoder.hpp
        cpp_encoder_path = cpp_base / "Encoder.hpp"
        encoder_template = EncoderTemplate(cpp_backend, strategy)
        was_written = write_if_changed(
            cpp_encoder_path, encoder_template.generate(self.registry, cpp_encoder_path)
        )
        stats.record_write(cpp_encoder_path, was_written)

        # Decoder.hpp
        cpp_decoder_path = cpp_base / "Decoder.hpp"
        decoder_template = DecoderTemplate(cpp_backend, strategy)
        was_written = write_if_changed(
            cpp_decoder_path, decoder_template.generate(self.registry, cpp_decoder_path)
        )
        stats.record_write(cpp_decoder_path, was_written)

        # ProtocolConstants.hpp
        cpp_constants_path = cpp_base / "ProtocolConstants.hpp"
        was_written = write_if_changed(
            cpp_constants_path,
            generate_constants_hpp(protocol_config_dict, self.registry, cpp_constants_path),
        )
        stats.record_write(cpp_constants_path, was_written)

        # MessageID.hpp
        cpp_messageid_path = cpp_base / "MessageID.hpp"
        was_written = write_if_changed(
            cpp_messageid_path,
            generate_messageid_hpp(
                self.messages, self.allocations, self.registry, cpp_messageid_path
            ),
        )
        stats.record_write(cpp_messageid_path, was_written)

        # MessageStructure.hpp
        cpp_message_structure_path = cpp_base / "MessageStructure.hpp"
        was_written = write_if_changed(
            cpp_message_structure_path,
            generate_message_structure_hpp(self.messages, cpp_message_structure_path),
        )
        stats.record_write(cpp_message_structure_path, was_written)

        # ProtocolCallbacks.hpp
        cpp_callbacks_path = cpp_base / "ProtocolCallbacks.hpp"
        was_written = write_if_changed(
            cpp_callbacks_path,
            generate_protocol_callbacks_hpp(self.messages, cpp_callbacks_path),
        )
        stats.record_write(cpp_callbacks_path, was_written)

        # DecoderRegistry.hpp
        cpp_decoder_registry_path = cpp_base / "DecoderRegistry.hpp"
        was_written = write_if_changed(
            cpp_decoder_registry_path,
            generate_decoder_registry_hpp(self.messages, cpp_decoder_registry_path),
        )
        stats.record_write(cpp_decoder_registry_path, was_written)

        # Protocol.hpp.template (uses protocol-specific renderer)
        cpp_protocol_template_path = cpp_base / "Protocol.hpp.template"
        protocol_renderer = components.get_cpp_protocol_renderer()
        was_written = write_if_changed(
            cpp_protocol_template_path,
            protocol_renderer.render(self.messages, cpp_protocol_template_path),
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
            was_written = write_if_changed(
                cpp_methods_path,
                generate_protocol_methods_hpp(new_style_messages, cpp_methods_path),
            )
            methods_stats.record_write(cpp_methods_path, was_written)

        # Generate struct files
        cpp_struct_dir = cpp_base / self.plugin_paths["output_cpp"]["structs"]
        cpp_struct_dir.mkdir(parents=True, exist_ok=True)

        struct_stats = GenerationStats()
        for message in self.messages:
            pascal_name = to_pascal_case(message.name)
            struct_name = f"{pascal_name}Message"
            cpp_output_path = cpp_struct_dir / f"{struct_name}.hpp"
            message_id = self.allocations[message.name]

            cpp_code = generate_struct_hpp(
                message,
                message_id,
                self.registry,
                cpp_output_path,
                self.protocol_config.limits.string_max_length,
                strategy,
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

    # =========================================================================
    # UNIFIED JAVA GENERATION
    # =========================================================================

    def _generate_java(self, output_base: Path) -> None:
        """
        Generate all Java files for this protocol.

        This is the unified implementation that works for all protocols.
        Protocol-specific behavior is delegated to:
        - get_components() for encoding strategy and renderers
        - _convert_config_to_java() for config conversion
        """
        if self.registry is None or self.plugin_paths is None or self.protocol_config is None:
            raise RuntimeError("Generator not properly initialized")

        components = self.get_components()
        strategy = components.get_encoding_strategy()

        stats = GenerationStats()

        java_base = output_base / self.plugin_paths["output_java"]["base_path"]
        java_base.mkdir(parents=True, exist_ok=True)

        java_package = self.plugin_paths["output_java"]["package"]
        struct_package = f"{java_package}.struct"
        protocol_config_dict = self._convert_config_to_java()

        # Generate base files using templates
        java_backend = JavaBackend(package=java_package)

        # Encoder.java
        java_encoder_path = java_base / "Encoder.java"
        encoder_template = EncoderTemplate(java_backend, strategy)
        was_written = write_if_changed(
            java_encoder_path,
            encoder_template.generate(self.registry, java_encoder_path),
        )
        stats.record_write(java_encoder_path, was_written)

        # Decoder.java
        java_decoder_path = java_base / "Decoder.java"
        decoder_template = DecoderTemplate(java_backend, strategy)
        was_written = write_if_changed(
            java_decoder_path,
            decoder_template.generate(self.registry, java_decoder_path),
        )
        stats.record_write(java_decoder_path, was_written)

        # ProtocolConstants.java
        java_constants_path = java_base / "ProtocolConstants.java"
        was_written = write_if_changed(
            java_constants_path,
            generate_constants_java(protocol_config_dict, java_constants_path, java_package),
        )
        stats.record_write(java_constants_path, was_written)

        # MessageID.java
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

        # ProtocolCallbacks.java
        java_callbacks_path = java_base / "ProtocolCallbacks.java"
        was_written = write_if_changed(
            java_callbacks_path,
            generate_protocol_callbacks_java(self.messages, java_package, java_callbacks_path),
        )
        stats.record_write(java_callbacks_path, was_written)

        # DecoderRegistry.java
        java_decoder_registry_path = java_base / "DecoderRegistry.java"
        was_written = write_if_changed(
            java_decoder_registry_path,
            generate_decoder_registry_java(
                self.messages, java_package, java_decoder_registry_path
            ),
        )
        stats.record_write(java_decoder_registry_path, was_written)

        # Protocol.java.template (uses protocol-specific renderer)
        java_protocol_template_path = java_base / "Protocol.java.template"
        protocol_renderer = components.get_java_protocol_renderer(java_package)
        was_written = write_if_changed(
            java_protocol_template_path,
            protocol_renderer.render(self.messages, java_protocol_template_path),
        )
        stats.record_write(java_protocol_template_path, was_written)

        # Generate enum files
        enum_stats = GenerationStats()
        for enum_def in self.enum_defs:
            java_enum_path = java_base / f"{enum_def.name}.java"
            java_enum_code = generate_enum_java(enum_def, java_enum_path, java_package)
            was_written = write_if_changed(java_enum_path, java_enum_code)
            enum_stats.record_write(java_enum_path, was_written)

        # Generate ProtocolMethods.java for new-style messages
        new_style_messages = [m for m in self.messages if not m.is_legacy()]
        methods_stats = GenerationStats()
        if new_style_messages:
            java_methods_path = java_base / "ProtocolMethods.java"
            was_written = write_if_changed(
                java_methods_path,
                generate_protocol_methods_java(
                    new_style_messages, java_methods_path, java_package, self.registry
                ),
            )
            methods_stats.record_write(java_methods_path, was_written)

        # Generate struct files
        java_struct_dir = java_base / self.plugin_paths["output_java"]["structs"]
        java_struct_dir.mkdir(parents=True, exist_ok=True)

        struct_stats = GenerationStats()
        for message in self.messages:
            pascal_name = to_pascal_case(message.name)
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
                strategy,
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

    # =========================================================================
    # STEP IMPLEMENTATIONS
    # =========================================================================

    def _step1_load_registry(self) -> None:
        """Step 1: Load type registry."""
        self._log("[1/7] Loading type registry...")
        self.registry = TypeRegistry()
        self.registry.load_builtins()
        type_names = list(self.registry.types.keys())
        populate_type_names(type_names)
        self._log(f"  ✓ Loaded {len(self.registry.types)} builtin types")

    def _step2_load_config(self, config_path: Path, plugin_paths_path: Path) -> None:
        """Step 2: Load configuration files."""
        self._log("[2/7] Loading configuration...")

        # Load protocol_config.py
        spec = importlib.util.spec_from_file_location("protocol_config", config_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {config_path}")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        self.protocol_config = config_module.PROTOCOL_CONFIG

        # Load plugin_paths.py
        spec = importlib.util.spec_from_file_location("plugin_paths", plugin_paths_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {plugin_paths_path}")
        paths_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(paths_module)
        self.plugin_paths = paths_module.PLUGIN_PATHS

        self._log("  ✓ Loaded protocol configuration")
        self._log_config_info()

    def _step3_import_messages(self, messages_dir: Path) -> None:
        """Step 3: Import message definitions."""
        self._log("[3/7] Importing messages...")

        # Add messages directory parent to sys.path temporarily for import
        messages_parent = str(messages_dir.parent)
        sys.path.insert(0, messages_parent)

        try:
            # Import message module dynamically
            message_module: ModuleType = importlib.import_module("message")
            if not hasattr(message_module, "ALL_MESSAGES"):
                raise ValueError("message module must define ALL_MESSAGES")

            all_messages: list[Message] = message_module.ALL_MESSAGES  # type: ignore[attr-defined]
            self._log(f"  ✓ Imported {len(all_messages)} messages")

            # Filter out deprecated messages
            self.messages = [m for m in all_messages if not m.deprecated]
            deprecated_count = len(all_messages) - len(self.messages)
            if deprecated_count > 0:
                self._log(f"  ⚠ Filtered out {deprecated_count} deprecated message(s)")

            # Collect enum definitions for later use
            self.enum_defs = collect_enum_defs(self.messages)
        finally:
            # Always clean up sys.path to avoid pollution
            if messages_parent in sys.path:
                sys.path.remove(messages_parent)

    def _step4_validate_messages(self) -> None:
        """Step 4: Validate messages."""
        self._log("[4/7] Validating messages...")

        if self.registry is None:
            raise RuntimeError("Registry not loaded")

        validator = ProtocolValidator(self.registry)
        errors = validator.validate_messages(self.messages)

        if errors:
            print("\n❌ Validation Errors:")
            for error in errors:
                print(f"  - {error}")
            raise ValueError(f"Protocol validation failed with {len(errors)} error(s)")

        self._log(f"  ✓ Validation passed ({len(self.messages)} messages)")

        # Protocol-specific validation
        protocol_errors = self._validate_protocol_specific()
        if protocol_errors:
            print(f"\n❌ {self.protocol_name} Validation Errors:")
            for error in protocol_errors:
                print(f"  - {error}")
            raise ValueError(
                f"{self.protocol_name} validation failed with {len(protocol_errors)} error(s)"
            )

    def _step5_allocate_ids(self) -> None:
        """Step 5: Allocate message IDs."""
        self._log("[5/7] Allocating message IDs...")
        self.allocations = allocate_message_ids(self.messages)
        self._log(
            f"  ✓ Allocated {len(self.allocations)} message IDs "
            f"(0x00-0x{len(self.allocations) - 1:02X})"
        )
