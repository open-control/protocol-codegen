"""
Enum definitions for protocol code generation.

This module provides the EnumDef class for defining shared enums
that are generated in both C++ and Java with identical values.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnumDef:
    """
    Definition of a shared enum for C++/Java code generation.

    EnumDef is the single source of truth for enum values that need
    to be synchronized between the controller (C++) and host (Java).

    Attributes:
        name: Enum name in PascalCase (e.g., "TrackType")
        values: Ordered mapping of enum value names to integer values
        description: Optional documentation for the enum
        string_mapping: Optional mapping from host API strings to enum names.
            If provided, generates fromString() helper in Java.
            Example: {"Audio": "AUDIO", "Instrument": "INSTRUMENT"}
        is_bitflags: If True, generates constants instead of enum class (for combinable flags)
        cpp_namespace: C++ namespace for the generated enum (default: none)

    Note:
        Java package is passed as parameter to generate_enum_java(), not stored here.
        This keeps EnumDef as pure data without output configuration.

    Examples:
        # Simple enum
        >>> TrackType = EnumDef(
        ...     name="TrackType",
        ...     values={"AUDIO": 0, "INSTRUMENT": 1, "GROUP": 2},
        ...     description="Type of track"
        ... )

        # Enum with string mapping (for host API conversion)
        >>> DeviceType = EnumDef(
        ...     name="DeviceType",
        ...     values={"UNKNOWN": 0, "AUDIO_EFFECT": 1, "INSTRUMENT": 2},
        ...     string_mapping={"audio-effect": "AUDIO_EFFECT", "instrument": "INSTRUMENT"}
        ... )

        # Bitflags (combinable values)
        >>> ChildType = EnumDef(
        ...     name="ChildType",
        ...     values={"NONE": 0, "SLOTS": 1, "LAYERS": 2, "DRUMS": 4},
        ...     is_bitflags=True
        ... )
    """

    name: str
    values: dict[str, int]
    description: str = ""
    string_mapping: dict[str, str] | None = None
    is_bitflags: bool = False
    cpp_namespace: str = ""

    def __post_init__(self) -> None:
        """Validate enum definition."""
        if not self.name:
            raise ValueError("Enum name cannot be empty")
        if not self.name[0].isupper():
            raise ValueError(f"Enum name must be PascalCase: {self.name}")
        if not self.values:
            raise ValueError(f"Enum '{self.name}' must have at least one value")

        # Validate all values are non-negative integers
        for val_name, val_int in self.values.items():
            if val_int < 0:
                raise ValueError(
                    f"Enum '{self.name}' value '{val_name}' must be a non-negative integer, got {val_int}"
                )

        # Validate string_mapping references valid enum values
        if self.string_mapping:
            for str_key, enum_name in self.string_mapping.items():
                if enum_name not in self.values:
                    raise ValueError(
                        f"Enum '{self.name}' string_mapping '{str_key}' -> '{enum_name}' "
                        f"references unknown value. Valid values: {list(self.values.keys())}"
                    )

    @property
    def max_value(self) -> int:
        """Return the maximum enum value."""
        return max(self.values.values())

    @property
    def wire_type(self) -> str:
        """Return the wire type for serialization (always uint8)."""
        return "uint8"

    @property
    def cpp_type(self) -> str:
        """Return the C++ type for this enum."""
        if self.is_bitflags:
            return "uint8_t"
        if self.cpp_namespace:
            return f"{self.cpp_namespace}::{self.name}"
        return self.name

    @property
    def java_type(self) -> str:
        """Return the Java type for this enum."""
        if self.is_bitflags:
            return "int"
        return self.name

    def get_default_value(self) -> str:
        """Return the name of the first/default enum value."""
        return next(iter(self.values.keys()))

    def __str__(self) -> str:
        """String representation for debugging."""
        flags_str = " (bitflags)" if self.is_bitflags else ""
        return f"EnumDef({self.name}{flags_str}: {list(self.values.keys())})"


__all__ = ["EnumDef"]
