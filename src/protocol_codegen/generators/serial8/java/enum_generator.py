"""
Java Enum Generator for Serial8 Protocol

Generates Java enum or constants from EnumDef definitions.
Enums are generated in the protocol package for consistency with structs.
"""

from pathlib import Path

from protocol_codegen.core.enum_def import EnumDef


def generate_enum_java(enum_def: EnumDef, output_path: Path) -> str:
    """
    Generate a Java file for an enum definition.

    For regular enums, generates a Java enum with getValue(), fromValue(),
    and optionally fromString() if string_mapping is provided.
    For bitflags, generates a class with static final int constants.

    Args:
        enum_def: The enum definition to generate
        output_path: Path where the file will be written (for header comment)

    Returns:
        Generated Java content as string

    Examples:
        >>> from protocol_codegen.core.enum_def import EnumDef
        >>> enum = EnumDef(name="TrackType", values={"AUDIO": 0, "INSTRUMENT": 1})
        >>> code = generate_enum_java(enum, Path("TrackType.java"))
        >>> "public enum TrackType" in code
        True
    """
    lines: list[str] = []

    # Package declaration
    lines.append(f"package {enum_def.java_package};")
    lines.append("")

    # Header comment
    lines.append(_generate_header(enum_def, output_path))

    if enum_def.is_bitflags:
        lines.append(_generate_bitflags_class(enum_def))
    else:
        lines.append(_generate_enum(enum_def))

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
        header_lines.append(f" * <p>{enum_def.description}</p>")
        header_lines.append(" *")

    if enum_def.is_bitflags:
        header_lines.append(" * <p>Note: This is a bitflags type - values can be combined with |</p>")
        header_lines.append(" *")

    header_lines.append(" */")

    return "\n".join(header_lines)


def _generate_enum(enum_def: EnumDef) -> str:
    """Generate Java enum with helpers."""
    lines: list[str] = []

    # Enum declaration
    lines.append(f"public enum {enum_def.name} {{")

    # Enum values
    value_entries = []
    for name, value in enum_def.values.items():
        value_entries.append(f"    {name}({value})")

    lines.append(",\n".join(value_entries) + ";")
    lines.append("")

    # Private field and constructor
    lines.append("    private final int value;")
    lines.append("")
    lines.append(f"    {enum_def.name}(int value) {{")
    lines.append("        this.value = value;")
    lines.append("    }")
    lines.append("")

    # getValue method
    lines.append("    /**")
    lines.append("     * Get the integer value for wire encoding.")
    lines.append("     * @return The enum value as int")
    lines.append("     */")
    lines.append("    public int getValue() {")
    lines.append("        return value;")
    lines.append("    }")
    lines.append("")

    # fromValue method
    default_value = enum_def.get_default_value()
    lines.append("    /**")
    lines.append("     * Convert from wire value to enum.")
    lines.append("     * @param value The integer value from wire")
    lines.append(f"     * @return The corresponding enum value, or {default_value} if unknown")
    lines.append("     */")
    lines.append(f"    public static {enum_def.name} fromValue(int value) {{")
    lines.append(f"        for ({enum_def.name} e : values()) {{")
    lines.append("            if (e.value == value) return e;")
    lines.append("        }")
    lines.append(f"        return {default_value};")
    lines.append("    }")

    # fromString method if mapping provided
    if enum_def.string_mapping:
        lines.append("")
        lines.append("    /**")
        lines.append("     * Convert from host API string to enum.")
        lines.append("     * @param str The string from host API")
        lines.append(f"     * @return The corresponding enum value, or {default_value} if unknown")
        lines.append("     */")
        lines.append(f"    public static {enum_def.name} fromString(String str) {{")
        lines.append("        if (str == null) return " + default_value + ";")
        lines.append("        switch (str) {")

        for str_key, enum_name in enum_def.string_mapping.items():
            lines.append(f'            case "{str_key}": return {enum_name};')

        lines.append(f"            default: return {default_value};")
        lines.append("        }")
        lines.append("    }")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _generate_bitflags_class(enum_def: EnumDef) -> str:
    """Generate Java class with static final int constants for bitflags."""
    lines: list[str] = []

    # Class declaration
    lines.append(f"public final class {enum_def.name} {{")
    lines.append("")
    lines.append("    // Private constructor - utility class")
    lines.append(f"    private {enum_def.name}() {{}}")
    lines.append("")

    # Constants
    for name, value in enum_def.values.items():
        lines.append(f"    public static final int {name} = {value};")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_enum_java"]
