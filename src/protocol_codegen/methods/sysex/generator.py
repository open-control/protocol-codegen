"""
SysEx Protocol Generator

Main orchestrator for SysEx protocol code generation.
Handles the complete generation pipeline from message definitions to generated code.
"""

import importlib
import importlib.util
import io
import sys
from pathlib import Path

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from typing import TYPE_CHECKING

from protocol_codegen.core.allocator import allocate_message_ids
from protocol_codegen.core.enum_def import EnumDef
from protocol_codegen.core.field import EnumField, populate_type_names
from protocol_codegen.core.file_utils import GenerationStats, write_if_changed
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message
from protocol_codegen.core.plugin_types import PluginPathsConfig
from protocol_codegen.core.validator import ProtocolValidator
from protocol_codegen.generators.sysex.cpp.callbacks_generator import (
    generate_protocol_callbacks_hpp,
)
from protocol_codegen.generators.sysex.cpp.constants_generator import (
    ProtocolConfig as CppProtocolConfig,
)
from protocol_codegen.generators.sysex.cpp.constants_generator import generate_constants_hpp
from protocol_codegen.generators.sysex.cpp.decoder_generator import generate_decoder_hpp
from protocol_codegen.generators.sysex.cpp.decoder_registry_generator import (
    generate_decoder_registry_hpp,
)
from protocol_codegen.generators.sysex.cpp.encoder_generator import generate_encoder_hpp
from protocol_codegen.generators.sysex.cpp.enum_generator import generate_enum_hpp
from protocol_codegen.generators.sysex.cpp.logger_generator import generate_logger_hpp
from protocol_codegen.generators.sysex.cpp.message_structure_generator import (
    generate_message_structure_hpp,
)
from protocol_codegen.generators.sysex.cpp.messageid_generator import generate_messageid_hpp
from protocol_codegen.generators.sysex.cpp.method_generator import generate_protocol_methods_hpp
from protocol_codegen.generators.sysex.cpp.protocol_generator import generate_protocol_template_hpp
from protocol_codegen.generators.sysex.cpp.struct_generator import generate_struct_hpp
from protocol_codegen.generators.sysex.java.callbacks_generator import (
    generate_protocol_callbacks_java,
)
from protocol_codegen.generators.sysex.java.constants_generator import (
    ProtocolConfig as JavaProtocolConfig,
)
from protocol_codegen.generators.sysex.java.constants_generator import generate_constants_java
from protocol_codegen.generators.sysex.java.decoder_generator import generate_decoder_java
from protocol_codegen.generators.sysex.java.decoder_registry_generator import (
    generate_decoder_registry_java,
)
from protocol_codegen.generators.sysex.java.encoder_generator import generate_encoder_java
from protocol_codegen.generators.sysex.java.enum_generator import generate_enum_java
from protocol_codegen.generators.sysex.java.messageid_generator import generate_messageid_java
from protocol_codegen.generators.sysex.java.method_generator import generate_protocol_methods_java
from protocol_codegen.generators.sysex.java.protocol_generator import (
    generate_protocol_template_java,
)
from protocol_codegen.generators.sysex.java.struct_generator import generate_struct_java
from protocol_codegen.methods.sysex.config import SysExConfig

if TYPE_CHECKING:
    from types import ModuleType


def _convert_sysex_config_to_cpp_protocol_config(config: SysExConfig) -> CppProtocolConfig:
    """Convert Pydantic SysExConfig to TypedDict ProtocolConfig for C++ generators."""
    return CppProtocolConfig(
        sysex={
            "start": config.framing.start,
            "end": config.framing.end,
            "manufacturer_id": config.framing.manufacturer_id,
            "device_id": config.framing.device_id,
            "min_message_length": config.structure.min_message_length,
            "message_type_offset": config.structure.message_type_offset,
            "from_host_offset": config.structure.from_host_offset,
            "payload_offset": config.structure.payload_offset,
        },
        limits={
            "string_max_length": config.limits.string_max_length,
            "array_max_items": config.limits.array_max_items,
            "max_payload_size": config.limits.max_payload_size,
            "max_message_size": config.limits.max_message_size,
        },
    )


def _convert_sysex_config_to_java_protocol_config(config: SysExConfig) -> JavaProtocolConfig:
    """Convert Pydantic SysExConfig to TypedDict ProtocolConfig for Java generators."""
    return JavaProtocolConfig(
        sysex={
            "start": config.framing.start,
            "end": config.framing.end,
            "manufacturer_id": config.framing.manufacturer_id,
            "device_id": config.framing.device_id,
            "min_message_length": config.structure.min_message_length,
            "message_type_offset": config.structure.message_type_offset,
            "from_host_offset": config.structure.from_host_offset,
            "payload_offset": config.structure.payload_offset,
        },
        limits={
            "string_max_length": config.limits.string_max_length,
            "array_max_items": config.limits.array_max_items,
            "max_payload_size": config.limits.max_payload_size,
            "max_message_size": config.limits.max_message_size,
        },
    )


def _validate_enum_values_for_sysex(enum_defs: list[EnumDef]) -> list[str]:
    """
    Validate that all enum values are ≤127 for 7-bit SysEx protocol.

    SysEx uses 7-bit encoding, so enum values must fit in a single byte
    with the high bit clear (0-127).

    Args:
        enum_defs: List of EnumDef instances to validate

    Returns:
        List of error messages (empty if all valid)
    """
    errors: list[str] = []
    max_value = 127  # 7-bit max

    for enum_def in enum_defs:
        for value_name, value in enum_def.values.items():
            if value > max_value:
                errors.append(
                    f"Enum '{enum_def.name}.{value_name}' has value {value} "
                    f"which exceeds SysEx 7-bit limit ({max_value})"
                )

    return errors


def _collect_enum_defs(messages: list[Message]) -> list[EnumDef]:
    """
    Collect all unique EnumDef instances from message fields.

    Traverses all messages and their fields (including nested composites)
    to find EnumField instances and extract their EnumDef references.

    Args:
        messages: List of Message instances to scan

    Returns:
        List of unique EnumDef instances (deduplicated by name)
    """
    from protocol_codegen.core.field import CompositeField

    seen_names: set[str] = set()
    enum_defs: list[EnumDef] = []

    def collect_from_fields(fields: list) -> None:
        """Recursively collect EnumDefs from a list of fields."""
        for field in fields:
            if isinstance(field, EnumField):
                if field.enum_def.name not in seen_names:
                    seen_names.add(field.enum_def.name)
                    enum_defs.append(field.enum_def)
            elif isinstance(field, CompositeField):
                # Recurse into composite fields
                collect_from_fields(list(field.fields))

    for message in messages:
        collect_from_fields(list(message.fields))

    return enum_defs


def generate_sysex_protocol(
    messages_dir: Path,
    config_path: Path,
    plugin_paths_path: Path,
    output_base: Path,
    verbose: bool = False,
) -> None:
    """
    Generate SysEx protocol code from message definitions.

    Args:
        messages_dir: Directory containing message definitions
        config_path: Path to protocol_config.py
        plugin_paths_path: Path to plugin_paths.py
        output_base: Base output directory
        verbose: Enable verbose output
    """

    def log(msg: str) -> None:
        """Print message if verbose."""
        if verbose:
            print(msg)

    # Step 1: Load type registry
    log("[1/7] Loading type registry...")
    registry = TypeRegistry()
    registry.load_builtins()
    type_names = list(registry.types.keys())
    populate_type_names(type_names)
    log(f"  ✓ Loaded {len(registry.types)} builtin types")

    # Step 2: Load configuration
    log("[2/7] Loading configuration...")

    # Load protocol_config.py
    spec = importlib.util.spec_from_file_location("protocol_config", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {config_path}")
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    protocol_config = config_module.PROTOCOL_CONFIG

    # Load plugin_paths.py
    spec = importlib.util.spec_from_file_location("plugin_paths", plugin_paths_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {plugin_paths_path}")
    paths_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paths_module)
    plugin_paths: PluginPathsConfig = paths_module.PLUGIN_PATHS

    log("  ✓ Loaded protocol configuration")
    log(f"  ✓ Manufacturer ID: 0x{protocol_config.framing.manufacturer_id:02X}")
    log(f"  ✓ Device ID: 0x{protocol_config.framing.device_id:02X}")

    # Step 3: Import messages
    log("[3/7] Importing messages...")

    # Add messages directory parent to sys.path temporarily for import
    messages_parent = str(messages_dir.parent)
    sys.path.insert(0, messages_parent)

    try:
        # Import message module dynamically
        message_module: ModuleType = importlib.import_module("message")
        if not hasattr(message_module, "ALL_MESSAGES"):
            raise ValueError("message module must define ALL_MESSAGES")

        all_messages: list[Message] = message_module.ALL_MESSAGES  # type: ignore[attr-defined]
        log(f"  ✓ Imported {len(all_messages)} messages")

        # Filter out deprecated messages
        messages = [m for m in all_messages if not m.deprecated]
        deprecated_count = len(all_messages) - len(messages)
        if deprecated_count > 0:
            log(f"  ⚠ Filtered out {deprecated_count} deprecated message(s)")
    finally:
        # Always clean up sys.path to avoid pollution
        if messages_parent in sys.path:
            sys.path.remove(messages_parent)

    # Step 4: Validate messages
    log("[4/7] Validating messages...")
    validator = ProtocolValidator(registry)
    errors = validator.validate_messages(messages)

    if errors:
        print("\n❌ Validation Errors:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError(f"Protocol validation failed with {len(errors)} error(s)")

    log(f"  ✓ Validation passed ({len(messages)} messages)")

    # Validate enum values for SysEx 7-bit constraint
    enum_defs = _collect_enum_defs(messages)
    if enum_defs:
        enum_errors = _validate_enum_values_for_sysex(enum_defs)
        if enum_errors:
            print("\n❌ SysEx Enum Validation Errors:")
            for error in enum_errors:
                print(f"  - {error}")
            raise ValueError(f"SysEx enum validation failed with {len(enum_errors)} error(s)")
        log(f"  ✓ Enum validation passed ({len(enum_defs)} enum(s), all values ≤127)")

    # Step 5: Allocate message IDs
    log("[5/7] Allocating message IDs...")
    allocations = allocate_message_ids(messages)
    log(f"  ✓ Allocated {len(allocations)} message IDs (0x00-0x{len(allocations) - 1:02X})")

    # Step 6: Generate C++ code
    log("[6/7] Generating C++ code...")
    _generate_cpp(
        messages=messages,
        allocations=allocations,
        registry=registry,
        protocol_config=protocol_config,
        plugin_paths=plugin_paths,
        output_base=output_base,
        verbose=verbose,
    )

    # Step 7: Generate Java code
    log("[7/7] Generating Java code...")
    _generate_java(
        messages=messages,
        allocations=allocations,
        registry=registry,
        protocol_config=protocol_config,
        plugin_paths=plugin_paths,
        output_base=output_base,
        verbose=verbose,
    )


def _generate_cpp(
    messages: list[Message],
    allocations: dict[str, int],
    registry: TypeRegistry,
    protocol_config: SysExConfig,
    plugin_paths: PluginPathsConfig,
    output_base: Path,
    verbose: bool,
) -> None:
    """Generate all C++ files with incremental generation (skip unchanged files)."""
    stats = GenerationStats()

    cpp_base = output_base / plugin_paths["output_cpp"]["base_path"]
    cpp_base.mkdir(parents=True, exist_ok=True)

    # Convert protocol config to TypedDict for generators
    protocol_config_dict = _convert_sysex_config_to_cpp_protocol_config(protocol_config)

    # Generate base files with incremental updates
    cpp_encoder_path = cpp_base / "Encoder.hpp"
    was_written = write_if_changed(
        cpp_encoder_path, generate_encoder_hpp(registry, cpp_encoder_path)
    )
    stats.record_write(cpp_encoder_path, was_written)

    cpp_decoder_path = cpp_base / "Decoder.hpp"
    was_written = write_if_changed(
        cpp_decoder_path, generate_decoder_hpp(registry, cpp_decoder_path)
    )
    stats.record_write(cpp_decoder_path, was_written)

    cpp_logger_path = cpp_base / "Logger.hpp"
    was_written = write_if_changed(cpp_logger_path, generate_logger_hpp(cpp_logger_path))
    stats.record_write(cpp_logger_path, was_written)

    cpp_constants_path = cpp_base / "ProtocolConstants.hpp"
    was_written = write_if_changed(
        cpp_constants_path,
        generate_constants_hpp(protocol_config_dict, registry, cpp_constants_path),
    )
    stats.record_write(cpp_constants_path, was_written)

    cpp_messageid_path = cpp_base / "MessageID.hpp"
    was_written = write_if_changed(
        cpp_messageid_path,
        generate_messageid_hpp(messages, allocations, registry, cpp_messageid_path),
    )
    stats.record_write(cpp_messageid_path, was_written)

    cpp_message_structure_path = cpp_base / "MessageStructure.hpp"
    was_written = write_if_changed(
        cpp_message_structure_path,
        generate_message_structure_hpp(messages, cpp_message_structure_path),
    )
    stats.record_write(cpp_message_structure_path, was_written)

    cpp_callbacks_path = cpp_base / "ProtocolCallbacks.hpp"
    was_written = write_if_changed(
        cpp_callbacks_path, generate_protocol_callbacks_hpp(messages, cpp_callbacks_path)
    )
    stats.record_write(cpp_callbacks_path, was_written)

    cpp_decoder_registry_path = cpp_base / "DecoderRegistry.hpp"
    was_written = write_if_changed(
        cpp_decoder_registry_path,
        generate_decoder_registry_hpp(messages, cpp_decoder_registry_path),
    )
    stats.record_write(cpp_decoder_registry_path, was_written)

    cpp_protocol_template_path = cpp_base / "Protocol.hpp.template"
    was_written = write_if_changed(
        cpp_protocol_template_path,
        generate_protocol_template_hpp(messages, cpp_protocol_template_path),
    )
    stats.record_write(cpp_protocol_template_path, was_written)

    # Generate enum files
    enum_defs = _collect_enum_defs(messages)
    enum_stats = GenerationStats()
    for enum_def in enum_defs:
        cpp_enum_path = cpp_base / f"{enum_def.name}.hpp"
        cpp_enum_code = generate_enum_hpp(enum_def, cpp_enum_path)
        was_written = write_if_changed(cpp_enum_path, cpp_enum_code)
        enum_stats.record_write(cpp_enum_path, was_written)

    # Generate ProtocolMethods.inl for new-style messages with direction
    new_style_messages = [m for m in messages if not m.is_legacy()]
    methods_stats = GenerationStats()
    if new_style_messages:
        cpp_methods_path = cpp_base / "ProtocolMethods.inl"
        cpp_methods_code = generate_protocol_methods_hpp(new_style_messages, cpp_methods_path)
        was_written = write_if_changed(cpp_methods_path, cpp_methods_code)
        methods_stats.record_write(cpp_methods_path, was_written)

    # Generate struct files (structs path is relative to base_path)
    cpp_struct_dir = cpp_base / plugin_paths["output_cpp"]["structs"]
    cpp_struct_dir.mkdir(parents=True, exist_ok=True)

    struct_stats = GenerationStats()
    for message in messages:
        pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
        struct_name = f"{pascal_name}Message"
        cpp_output_path = cpp_struct_dir / f"{struct_name}.hpp"
        message_id = allocations[message.name]

        cpp_code = generate_struct_hpp(
            message, message_id, registry, cpp_output_path, protocol_config.limits.string_max_length
        )
        was_written = write_if_changed(cpp_output_path, cpp_code)
        struct_stats.record_write(cpp_output_path, was_written)

    if verbose:
        print(f"  ✓ C++ base files: {stats.summary()}")
        if enum_defs:
            print(f"  ✓ C++ enum files: {enum_stats.summary()}")
        if new_style_messages:
            print(f"  ✓ C++ ProtocolMethods.inl: {methods_stats.summary()}")
        print(f"  ✓ C++ struct files: {struct_stats.summary()}")
        print(f"  → Output: {cpp_base.relative_to(output_base)}")


def _generate_java(
    messages: list[Message],
    allocations: dict[str, int],
    registry: TypeRegistry,
    protocol_config: SysExConfig,
    plugin_paths: PluginPathsConfig,
    output_base: Path,
    verbose: bool,
) -> None:
    """Generate all Java files with incremental generation (skip unchanged files)."""
    stats = GenerationStats()

    java_base = output_base / plugin_paths["output_java"]["base_path"]
    java_base.mkdir(parents=True, exist_ok=True)

    # Extract Java package from plugin_paths
    java_package = plugin_paths["output_java"]["package"]
    java_struct_package = f"{java_package}.struct"

    # Convert protocol config to TypedDict for generators
    protocol_config_dict = _convert_sysex_config_to_java_protocol_config(protocol_config)

    # Generate base files with incremental updates
    java_encoder_path = java_base / "Encoder.java"
    was_written = write_if_changed(
        java_encoder_path, generate_encoder_java(registry, java_encoder_path, java_package)
    )
    stats.record_write(java_encoder_path, was_written)

    java_decoder_path = java_base / "Decoder.java"
    was_written = write_if_changed(
        java_decoder_path, generate_decoder_java(registry, java_decoder_path, java_package)
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
        generate_messageid_java(messages, allocations, registry, java_messageid_path, java_package),
    )
    stats.record_write(java_messageid_path, was_written)

    java_callbacks_path = java_base / "ProtocolCallbacks.java"
    was_written = write_if_changed(
        java_callbacks_path,
        generate_protocol_callbacks_java(messages, java_package, java_callbacks_path),
    )
    stats.record_write(java_callbacks_path, was_written)

    java_decoder_registry_path = java_base / "DecoderRegistry.java"
    was_written = write_if_changed(
        java_decoder_registry_path,
        generate_decoder_registry_java(messages, java_package, java_decoder_registry_path),
    )
    stats.record_write(java_decoder_registry_path, was_written)

    java_protocol_template_path = java_base / "Protocol.java.template"
    was_written = write_if_changed(
        java_protocol_template_path,
        generate_protocol_template_java(messages, java_protocol_template_path, java_package),
    )
    stats.record_write(java_protocol_template_path, was_written)

    # Generate enum files
    enum_defs = _collect_enum_defs(messages)
    enum_stats = GenerationStats()
    for enum_def in enum_defs:
        java_enum_path = java_base / f"{enum_def.name}.java"
        java_enum_code = generate_enum_java(enum_def, java_enum_path)
        was_written = write_if_changed(java_enum_path, java_enum_code)
        enum_stats.record_write(java_enum_path, was_written)

    # Generate ProtocolMethods.java for new-style messages with direction
    new_style_messages = [m for m in messages if not m.is_legacy()]
    methods_stats = GenerationStats()
    if new_style_messages:
        java_methods_path = java_base / "ProtocolMethods.java"
        java_methods_code = generate_protocol_methods_java(
            new_style_messages, java_methods_path, java_package, registry
        )
        was_written = write_if_changed(java_methods_path, java_methods_code)
        methods_stats.record_write(java_methods_path, was_written)

    # Generate struct files (structs path is relative to base_path)
    java_struct_dir = java_base / plugin_paths["output_java"]["structs"]
    java_struct_dir.mkdir(parents=True, exist_ok=True)

    struct_stats = GenerationStats()
    for message in messages:
        pascal_name = "".join(word.capitalize() for word in message.name.split("_"))
        class_name = f"{pascal_name}Message"
        java_output_path = java_struct_dir / f"{class_name}.java"
        message_id = allocations[message.name]

        java_code = generate_struct_java(
            message,
            message_id,
            registry,
            java_output_path,
            protocol_config.limits.string_max_length,
            java_struct_package,
        )
        was_written = write_if_changed(java_output_path, java_code)
        struct_stats.record_write(java_output_path, was_written)

    if verbose:
        print(f"  ✓ Java base files: {stats.summary()}")
        if enum_defs:
            print(f"  ✓ Java enum files: {enum_stats.summary()}")
        if new_style_messages:
            print(f"  ✓ Java ProtocolMethods.java: {methods_stats.summary()}")
        print(f"  ✓ Java struct files: {struct_stats.summary()}")
        print(f"  → Output: {java_base.relative_to(output_base)}")
