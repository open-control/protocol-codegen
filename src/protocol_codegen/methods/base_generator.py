"""
Base Protocol Generator

Abstract base class providing the common generation pipeline.
Serial8Generator and SysExGenerator inherit from this.
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
from protocol_codegen.core.loader import TypeRegistry
from protocol_codegen.core.message import Message
from protocol_codegen.core.plugin_types import PluginPathsConfig
from protocol_codegen.core.validator import ProtocolValidator
from protocol_codegen.methods.common import collect_enum_defs

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

    Subclasses implement protocol-specific behavior via abstract methods.
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

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Return protocol name for logging (e.g., 'Serial8', 'SysEx')."""
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
    def _generate_cpp(self, output_base: Path) -> None:
        """Generate all C++ files for this protocol."""
        ...

    @abstractmethod
    def _generate_java(self, output_base: Path) -> None:
        """Generate all Java files for this protocol."""
        ...

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
