"""
SysEx Protocol Generator

Main orchestrator for SysEx protocol code generation.
Handles the complete generation pipeline from message definitions to generated code.
"""

import sys
import io
import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Dict, List

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.validator import ProtocolValidator
from protocol_codegen.core.allocator import allocate_message_ids
from protocol_codegen.core.field import populate_type_names
from protocol_codegen.core.message import Message

from protocol_codegen.generators.cpp.struct_generator import generate_struct_hpp
from protocol_codegen.generators.cpp.messageid_generator import generate_messageid_hpp
from protocol_codegen.generators.cpp.encoder_generator import generate_encoder_hpp
from protocol_codegen.generators.cpp.decoder_generator import generate_decoder_hpp
from protocol_codegen.generators.cpp.constants_generator import generate_constants_hpp
from protocol_codegen.generators.cpp.logger_generator import generate_logger_hpp

from protocol_codegen.generators.java.struct_generator import generate_struct_java
from protocol_codegen.generators.java.messageid_generator import generate_messageid_java
from protocol_codegen.generators.java.encoder_generator import generate_encoder_java
from protocol_codegen.generators.java.decoder_generator import generate_decoder_java
from protocol_codegen.generators.java.constants_generator import generate_constants_java


def generate_sysex_protocol(
    messages_dir: Path,
    config_path: Path,
    plugin_paths_path: Path,
    output_base: Path,
    verbose: bool = False
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
    plugin_paths = paths_module.PLUGIN_PATHS

    log(f"  ✓ Loaded protocol configuration")
    log(f"  ✓ Manufacturer ID: 0x{protocol_config.framing.manufacturer_id:02X}")
    log(f"  ✓ Device ID: 0x{protocol_config.framing.device_id:02X}")

    # Step 3: Import messages
    log("[3/7] Importing messages...")

    # Add messages directory to path
    sys.path.insert(0, str(messages_dir.parent))

    # Import message module dynamically
    message_module: ModuleType = importlib.import_module('message')
    if not hasattr(message_module, 'ALL_MESSAGES'):
        raise ValueError("message module must define ALL_MESSAGES")

    messages: List[Message] = message_module.ALL_MESSAGES  # type: ignore[attr-defined]
    log(f"  ✓ Imported {len(messages)} messages")

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

    # Step 5: Allocate message IDs
    log("[5/7] Allocating message IDs...")
    allocations = allocate_message_ids(messages)
    log(f"  ✓ Allocated {len(allocations)} message IDs (0x00-0x{len(allocations)-1:02X})")

    # Step 6: Generate C++ code
    log("[6/7] Generating C++ code...")
    _generate_cpp(
        messages=messages,
        allocations=allocations,
        registry=registry,
        protocol_config=protocol_config,
        plugin_paths=plugin_paths,
        output_base=output_base,
        verbose=verbose
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
        verbose=verbose
    )


def _generate_cpp(
    messages: List[Message],
    allocations: Dict[str, int],
    registry: TypeRegistry,
    protocol_config,
    plugin_paths: dict,
    output_base: Path,
    verbose: bool
) -> None:
    """Generate all C++ files."""

    cpp_base = output_base / plugin_paths['output_cpp']['base_path']
    cpp_base.mkdir(parents=True, exist_ok=True)

    # Convert protocol config to dict for generators
    protocol_config_dict = {
        'sysex': {
            'start': protocol_config.framing.start,
            'end': protocol_config.framing.end,
            'manufacturer_id': protocol_config.framing.manufacturer_id,
            'device_id': protocol_config.framing.device_id,
            'min_message_length': protocol_config.structure.min_message_length,
            'message_type_offset': protocol_config.structure.message_type_offset,
            'from_host_offset': protocol_config.structure.from_host_offset,
            'payload_offset': protocol_config.structure.payload_offset,
        },
        'limits': {
            'string_max_length': protocol_config.limits.string_max_length,
            'array_max_items': protocol_config.limits.array_max_items,
            'max_payload_size': protocol_config.limits.max_payload_size,
            'max_message_size': protocol_config.limits.max_message_size,
        },
        'roles': {
            'cpp': 'controller',
            'java': 'host',
        }
    }

    # Generate base files
    files_generated = []

    cpp_encoder_path = cpp_base / "Encoder.hpp"
    cpp_encoder_path.write_text(generate_encoder_hpp(registry, cpp_encoder_path), encoding='utf-8')
    files_generated.append("Encoder.hpp")

    cpp_decoder_path = cpp_base / "Decoder.hpp"
    cpp_decoder_path.write_text(generate_decoder_hpp(registry, cpp_decoder_path), encoding='utf-8')
    files_generated.append("Decoder.hpp")

    cpp_logger_path = cpp_base / "Logger.hpp"
    cpp_logger_path.write_text(generate_logger_hpp(cpp_logger_path), encoding='utf-8')
    files_generated.append("Logger.hpp")

    cpp_constants_path = cpp_base / "ProtocolConstants.hpp"
    cpp_constants_path.write_text(generate_constants_hpp(protocol_config_dict, registry, cpp_constants_path), encoding='utf-8')
    files_generated.append("ProtocolConstants.hpp")

    cpp_messageid_path = cpp_base / "MessageID.hpp"
    cpp_messageid_path.write_text(generate_messageid_hpp(messages, allocations, registry, cpp_messageid_path), encoding='utf-8')
    files_generated.append("MessageID.hpp")

    # Generate struct files
    cpp_struct_dir = output_base / plugin_paths['output_cpp']['structs']
    cpp_struct_dir.mkdir(parents=True, exist_ok=True)

    for message in messages:
        pascal_name = ''.join(word.capitalize() for word in message.name.split('_'))
        struct_name = f"{pascal_name}Message"
        cpp_output_path = cpp_struct_dir / f"{struct_name}.hpp"
        message_id = allocations[message.name]

        cpp_code = generate_struct_hpp(
            message,
            message_id,
            registry,
            cpp_output_path,
            protocol_config.limits.string_max_length
        )
        cpp_output_path.write_text(cpp_code, encoding='utf-8')

    if verbose:
        print(f"  ✓ Generated {len(files_generated)} C++ base files")
        print(f"  ✓ Generated {len(messages)} C++ struct files")
        print(f"  → Output: {cpp_base.relative_to(output_base)}")


def _generate_java(
    messages: List[Message],
    allocations: Dict[str, int],
    registry: TypeRegistry,
    protocol_config,
    plugin_paths: dict,
    output_base: Path,
    verbose: bool
) -> None:
    """Generate all Java files."""

    java_base = output_base / plugin_paths['output_java']['base_path']
    java_base.mkdir(parents=True, exist_ok=True)

    # Convert protocol config to dict for generators
    protocol_config_dict = {
        'sysex': {
            'start': protocol_config.framing.start,
            'end': protocol_config.framing.end,
            'manufacturer_id': protocol_config.framing.manufacturer_id,
            'device_id': protocol_config.framing.device_id,
            'min_message_length': protocol_config.structure.min_message_length,
            'message_type_offset': protocol_config.structure.message_type_offset,
            'from_host_offset': protocol_config.structure.from_host_offset,
            'payload_offset': protocol_config.structure.payload_offset,
        },
        'limits': {
            'string_max_length': protocol_config.limits.string_max_length,
            'array_max_items': protocol_config.limits.array_max_items,
            'max_payload_size': protocol_config.limits.max_payload_size,
            'max_message_size': protocol_config.limits.max_message_size,
        },
        'roles': {
            'cpp': 'controller',
            'java': 'host',
        }
    }

    # Generate base files
    files_generated = []

    java_encoder_path = java_base / "Encoder.java"
    java_encoder_path.write_text(generate_encoder_java(registry, java_encoder_path), encoding='utf-8')
    files_generated.append("Encoder.java")

    java_decoder_path = java_base / "Decoder.java"
    java_decoder_path.write_text(generate_decoder_java(registry, java_decoder_path), encoding='utf-8')
    files_generated.append("Decoder.java")

    java_constants_path = java_base / "ProtocolConstants.java"
    java_constants_path.write_text(generate_constants_java(protocol_config_dict, java_constants_path), encoding='utf-8')
    files_generated.append("ProtocolConstants.java")

    java_messageid_path = java_base / "MessageID.java"
    java_messageid_path.write_text(generate_messageid_java(messages, allocations, registry, java_messageid_path), encoding='utf-8')
    files_generated.append("MessageID.java")

    # Generate struct files
    java_struct_dir = output_base / plugin_paths['output_java']['structs']
    java_struct_dir.mkdir(parents=True, exist_ok=True)

    for message in messages:
        pascal_name = ''.join(word.capitalize() for word in message.name.split('_'))
        class_name = f"{pascal_name}Message"
        java_output_path = java_struct_dir / f"{class_name}.java"
        message_id = allocations[message.name]

        java_code = generate_struct_java(
            message,
            message_id,
            registry,
            java_output_path,
            protocol_config.limits.string_max_length
        )
        java_output_path.write_text(java_code, encoding='utf-8')

    if verbose:
        print(f"  ✓ Generated {len(files_generated)} Java base files")
        print(f"  ✓ Generated {len(messages)} Java class files")
        print(f"  → Output: {java_base.relative_to(output_base)}")
