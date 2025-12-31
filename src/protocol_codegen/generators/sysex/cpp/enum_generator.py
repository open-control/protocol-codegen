"""
C++ Enum Generator for SysEx Protocol

Generates C++ enum class or constants from EnumDef definitions.
Enums are generated in the Protocol namespace for consistency with structs.
"""

from pathlib import Path

from protocol_codegen.core.enum_def import EnumDef


def generate_enum_hpp(enum_def: EnumDef, output_path: Path) -> str:
    """
    Generate a C++ header file for an enum definition.

    For regular enums, generates an enum class with conversion helpers.
    For bitflags, generates constexpr constants that can be combined with |.

    Args:
        enum_def: The enum definition to generate
        output_path: Path where the file will be written (for header comment)

    Returns:
        Generated C++ header content as string

    Examples:
        >>> from protocol_codegen.core.enum_def import EnumDef
        >>> enum = EnumDef(name="TrackType", values={"AUDIO": 0, "INSTRUMENT": 1})
        >>> code = generate_enum_hpp(enum, Path("TrackType.hpp"))
        >>> "enum class TrackType" in code
        True
    """
    lines: list[str] = []

    # Header
    lines.append(_generate_header(enum_def, output_path))

    # Pragma and includes
    lines.append("#pragma once")
    lines.append("")
    lines.append("#include <cstdint>")
    lines.append("")

    # Open namespace (if specified)
    if enum_def.cpp_namespace:
        lines.append(f"namespace {enum_def.cpp_namespace} {{")
        lines.append("")

    if enum_def.is_bitflags:
        lines.append(_generate_bitflags(enum_def))
    else:
        lines.append(_generate_enum_class(enum_def))

    # Close namespace (if specified)
    if enum_def.cpp_namespace:
        lines.append(f"}}  // namespace {enum_def.cpp_namespace}")
        lines.append("")

    return "\n".join(lines)


def _generate_header(enum_def: EnumDef, output_path: Path) -> str:
    """Generate file header comment."""
    header_lines = [
        "/**",
        f" * {output_path.name} - Auto-generated Protocol Enum",
        " *",
        " * AUTO-GENERATED - DO NOT EDIT",
        " *",
    ]

    if enum_def.description:
        header_lines.append(f" * Description: {enum_def.description}")
        header_lines.append(" *")

    if enum_def.is_bitflags:
        header_lines.append(" * Note: This is a bitflags type - values can be combined with |")
        header_lines.append(" *")

    header_lines.append(" */")
    header_lines.append("")

    return "\n".join(header_lines)


def _generate_enum_class(enum_def: EnumDef) -> str:
    """Generate enum class with conversion helpers."""
    lines: list[str] = []

    # Enum class definition
    lines.append(f"enum class {enum_def.name} : uint8_t {{")

    # Values
    for name, value in enum_def.values.items():
        lines.append(f"    {name} = {value},")

    lines.append("};")
    lines.append("")

    # Conversion helpers
    lines.append("// Conversion helpers")
    lines.append(f"inline {enum_def.name} to{enum_def.name}(uint8_t value) {{")
    lines.append(f"    return static_cast<{enum_def.name}>(value);")
    lines.append("}")
    lines.append("")

    lines.append(f"inline uint8_t from{enum_def.name}({enum_def.name} value) {{")
    lines.append("    return static_cast<uint8_t>(value);")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _generate_bitflags(enum_def: EnumDef) -> str:
    """Generate constexpr constants for bitflags."""
    lines: list[str] = []

    # Constants
    lines.append(f"// {enum_def.name} bitflags - combine with |")
    for name, value in enum_def.values.items():
        const_name = f"{_to_screaming_snake(enum_def.name)}_{name}"
        lines.append(f"constexpr uint8_t {const_name} = {value};")

    lines.append("")

    return "\n".join(lines)


def _to_screaming_snake(pascal_case: str) -> str:
    """Convert PascalCase to SCREAMING_SNAKE_CASE.

    Examples:
        >>> _to_screaming_snake("TrackType")
        'TRACK_TYPE'
        >>> _to_screaming_snake("ChildType")
        'CHILD_TYPE'
    """
    result: list[str] = []
    for i, char in enumerate(pascal_case):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.upper())
    return "".join(result)


__all__ = ["generate_enum_hpp"]
