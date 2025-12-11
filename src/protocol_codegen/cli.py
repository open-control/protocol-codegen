#!/usr/bin/env python3
"""
Protocol CodeGen - CLI Interface

Command-line interface for generating protocol code from message definitions.
"""

import sys
from pathlib import Path

import click


@click.group()
@click.version_option(version="1.0.0", prog_name="protocol-codegen")
def cli():
    """
    Protocol CodeGen - Generate type-safe Sysex protocol code from message definitions in C++ and Java
    """
    pass


@cli.command()
@click.option(
    "--method",
    type=click.Choice(["sysex"], case_sensitive=False),
    required=True,
    help="Protocol method to use (sysex, osc, etc.)",
)
@click.option(
    "--messages",
    type=click.Path(exists=True),
    required=True,
    help="Path to message directory or __init__.py file",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to protocol_config.py file",
)
@click.option(
    "--plugin-paths",
    type=click.Path(exists=True),
    required=True,
    help="Path to plugin_paths.py file",
)
@click.option(
    "--output-base",
    type=click.Path(),
    required=True,
    help="Base output directory (contains plugin_paths config)",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def generate(
    method: str, messages: str, config: str, plugin_paths: str, output_base: str, verbose: bool
):
    """
    Generate protocol code from message definitions.

    Examples:

        # Generate from example directory
        protocol-codegen generate --method sysex \\
            --messages ./examples/simple-sensor-network/message \\
            --config ./examples/simple-sensor-network/protocol_config.py \\
            --plugin-paths ./examples/simple-sensor-network/plugin_paths.py \\
            --output-base ./examples/simple-sensor-network
    """
    # Convert string paths to Path objects
    messages_path = Path(messages)
    config_path = Path(config)
    plugin_paths_path = Path(plugin_paths)
    output_base_path = Path(output_base)

    if verbose:
        click.echo("=" * 70)
        click.echo("Protocol CodeGen v1.0.0")
        click.echo("=" * 70)
        click.echo(f"Method: {method}")
        click.echo(f"Messages: {messages_path}")
        click.echo(f"Config: {config_path}")
        click.echo(f"Plugin paths: {plugin_paths_path}")
        click.echo(f"Output base: {output_base_path}")
        click.echo()

    # Import generator based on method
    if method.lower() == "sysex":
        from protocol_codegen.methods.sysex.generator import generate_sysex_protocol

        try:
            generate_sysex_protocol(
                messages_dir=messages_path,
                config_path=config_path,
                plugin_paths_path=plugin_paths_path,
                output_base=output_base_path,
                verbose=verbose,
            )
            if verbose:
                click.echo()
                click.echo("=" * 70)
            click.echo("✅ Code generation completed successfully!")
            if verbose:
                click.echo("=" * 70)
        except Exception as e:
            click.echo(f"❌ Error during generation: {e}", err=True)
            if verbose:
                import traceback

                traceback.print_exc()
            sys.exit(1)
    else:
        click.echo(f"❌ Method '{method}' not yet implemented", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--method",
    type=click.Choice(["sysex"], case_sensitive=False),
    required=True,
    help="Protocol method to validate for",
)
@click.option(
    "--messages",
    type=click.Path(exists=True),
    required=True,
    help="Path to message directory containing __init__.py with ALL_MESSAGES",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def validate(method: str, messages: str, verbose: bool):
    """
    Validate message definitions without generating code.

    Performs validation checks including:
    - Field types reference existing atomic types
    - No duplicate message names
    - No duplicate field names within messages
    - Composite field depth limits

    Examples:

        protocol-codegen validate --method sysex --messages ./message
        protocol-codegen validate --method sysex --messages ./message --verbose
    """
    import importlib

    from protocol_codegen.core.field import populate_type_names
    from protocol_codegen.core.loader import TypeRegistry
    from protocol_codegen.core.message import Message
    from protocol_codegen.core.validator import ProtocolValidator

    messages_path = Path(messages)

    click.echo(f"🔍 Validating messages: {messages_path}")
    click.echo(f"   Method: {method}")
    click.echo()

    try:
        # Step 1: Load type registry
        if verbose:
            click.echo("[1/3] Loading type registry...")
        registry = TypeRegistry()
        registry.load_builtins()
        type_names = list(registry.types.keys())
        populate_type_names(type_names)
        if verbose:
            click.echo(f"      ✓ Loaded {len(registry.types)} builtin types")

        # Step 2: Import messages
        if verbose:
            click.echo("[2/3] Importing messages...")

        # Add messages directory parent to path for imports
        messages_parent = messages_path.parent if messages_path.is_file() else messages_path.parent
        sys.path.insert(0, str(messages_parent))

        try:
            # Determine module name
            module_name = messages_path.stem if messages_path.is_file() else messages_path.name

            # Import the message module
            message_module = importlib.import_module(module_name)

            if not hasattr(message_module, "ALL_MESSAGES"):
                click.echo("❌ Error: message module must define ALL_MESSAGES", err=True)
                sys.exit(1)

            loaded_messages: list[Message] = message_module.ALL_MESSAGES
            if verbose:
                click.echo(f"      ✓ Loaded {len(loaded_messages)} messages")

        finally:
            # Clean up sys.path
            sys.path.remove(str(messages_parent))

        # Step 3: Validate messages
        if verbose:
            click.echo("[3/3] Validating messages...")

        validator = ProtocolValidator(registry)
        errors = validator.validate_messages(loaded_messages)

        if errors:
            click.echo()
            click.echo("❌ Validation failed with errors:", err=True)
            click.echo()
            for error in errors:
                click.echo(f"   • {error}", err=True)
            click.echo()
            sys.exit(1)

        # Success
        click.echo()
        click.echo(f"✅ Validation passed! ({len(loaded_messages)} messages)")

        if verbose:
            click.echo()
            click.echo("   Messages validated:")
            for msg in sorted(loaded_messages, key=lambda m: m.name):
                field_count = len(msg.fields)
                click.echo(f"   • {msg.name} ({field_count} fields)")

    except Exception as e:
        click.echo(f"❌ Error during validation: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command(name="list-methods")
def list_methods():
    """List available protocol methods."""
    click.echo("📋 Available Protocol Methods:")
    click.echo()
    click.echo("  ✅ sysex    - MIDI System Exclusive protocol")
    click.echo("  🔮 osc      - Open Sound Control (planned)")
    click.echo("  🔮 custom   - Custom binary protocol (planned)")
    click.echo()


@cli.command(name="list-generators")
def list_generators():
    """List available code generators."""
    click.echo("📋 Available Code Generators:")
    click.echo()
    click.echo("  ✅ C++         - For embedded systems, audio plugins, native apps")
    click.echo("  ✅ Java        - For desktop apps, Android, host extensions")
    click.echo("  🔮 Rust        - (planned)")
    click.echo("  🔮 Python      - (planned)")
    click.echo("  🔮 TypeScript  - (planned)")
    click.echo()


@cli.command()
@click.option(
    "--method",
    type=click.Choice(["sysex"], case_sensitive=False),
    default="sysex",
    help="Protocol method for scaffolding",
)
@click.option(
    "--generators", default="cpp,java", help="Comma-separated list of generators (e.g., cpp,java)"
)
@click.option(
    "--output",
    type=click.Path(),
    default="./my-protocol",
    help="Output directory for scaffolding",
)
def init(method: str, generators: str, output: str):
    """
    Initialize a new protocol project with scaffolding.

    Examples:

        # Create new SysEx project with C++ and Java
        protocol-codegen init --method sysex --generators cpp,java --output ./my-protocol
    """
    output_path = Path(output)

    click.echo("🏗️  Initializing new protocol project")
    click.echo(f"Method: {method}")
    click.echo(f"Generators: {generators}")
    click.echo(f"Output: {output_path}")

    # TODO: Implement scaffolding
    click.echo("⚠️  Scaffolding not yet implemented")
    sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
