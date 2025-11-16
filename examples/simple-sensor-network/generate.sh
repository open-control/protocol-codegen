#!/bin/bash

# Generate protocol code for simple-sensor-network example

SCRIPT_DIR="$(dirname "$0")"

protocol-codegen generate \
    --method sysex \
    --messages "$SCRIPT_DIR/message" \
    --config "$SCRIPT_DIR/protocol_config.py" \
    --plugin-paths "$SCRIPT_DIR/plugin_paths.py" \
    --output-base "$SCRIPT_DIR" \
    --verbose
