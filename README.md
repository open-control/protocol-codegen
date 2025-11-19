# Protocol CodeGen

Generate type-safe protocol code (C++, Java) from Python message definitions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked with pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

## Features

- **SysEx protocol** - MIDI System Exclusive
- **Type-safe** - Compile-time error detection
- **Bidirectional** - C++ ↔ Java communication
- **Auto ID allocation** - Sequential message IDs
- **Validation** - Strict message validation

## Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **uv** - Fast Python package manager ([Installation](https://github.com/astral-sh/uv))

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
# Or: pip install uv                               # Windows/any platform
```

## Installation

```bash
# Clone the repository
git clone https://github.com/petitechose-audio/protocol-codegen.git
cd protocol-codegen

# Install dependencies and package
uv sync
```

## Quick Start

```bash
# Generate from example
cd examples/simple-sensor-network
./generate.sh
```

## Define Messages

**field/sensor.py:**
```python
from protocol_codegen.core.field import PrimitiveField, Type

sensor_id = PrimitiveField('sensorId', type_name=Type.UINT8)
sensor_value = PrimitiveField('value', type_name=Type.FLOAT32)
```

**message/sensor.py:**
```python
from protocol_codegen.core.message import Message
from field.sensor import *

SENSOR_READING = Message(
    description='Single sensor reading',
    fields=[sensor_id, sensor_value]
)
```

**message/__init__.py:**
```python
from .sensor import *

ALL_MESSAGES = [SENSOR_READING]

# Auto-inject message names
for name, msg in globals().items():
    if isinstance(msg, Message):
        msg.name = name
```

## Configure

**protocol_config.py:**
```python
from protocol_codegen.methods.sysex import SysExConfig, SysExLimits, SysExFraming

PROTOCOL_CONFIG = SysExConfig(
    framing=SysExFraming(
        manufacturer_id=0x7D,
        device_id=0x42,
    ),
    limits=SysExLimits(
        max_message_size=512,
        string_max_length=32,
    )
)
```

**plugin_paths.py:**
```python
PLUGIN_PATHS = {
    'output_cpp': {
        'base_path': 'generated/cpp',
        'namespace': 'Protocol',     # C++ namespace
        'structs': 'struct/',        # Relative to base_path
    },
    'output_java': {
        'base_path': 'generated/java',
        'package': 'protocol',       # Java package
        'structs': 'struct/',        # Relative to base_path
    },
}
```

## Generate

```bash
protocol-codegen generate \
    --method sysex \
    --messages message \
    --config protocol_config.py \
    --plugin-paths plugin_paths.py \
    --output-base . \
    --verbose
```

## Use Generated Code

**C++:**
```cpp
#include "Encoder.hpp"
#include "struct/SensorReadingMessage.hpp"

SensorReadingMessage msg;
msg.sensorId = 1;
msg.value = 23.5f;

uint8_t buffer[64];
size_t len = Protocol::Encoder::encode(msg, buffer);
Serial.write(buffer, len);
```

**Java:**
```java
import Decoder;
import struct.SensorReadingMessage;

byte[] data = midiInput.readSysEx();
SensorReadingMessage msg = Decoder.decodeSensorReading(data);
System.out.println("Value: " + msg.value);
```

## Examples

See `examples/simple-sensor-network/` for a complete example with:
- 10 messages
- Nested composite types
- Arrays
- Full C++ and Java generation

## Development

### Setup Development Environment

```bash
# Install package with development dependencies
uv sync --extra dev

# Verify installation
make all
```

### Development Dependencies

The `dev` extra includes:
- **ruff** - Fast linter and formatter
- **pyright** - Static type checker (strict mode)
- **types-click** - Type stubs for Click

### Available Commands

```bash
make help          # Show all available commands
make sync          # Sync all dependencies (including dev)
make format        # Format code with ruff
make lint          # Lint code with ruff
make type-check    # Type check with pyright
make all           # Run format, lint, type-check
make example       # Run example generation
make clean         # Clean build artifacts
```

### Quick Development Workflow

```bash
# Make changes to code
make format        # Auto-format code
make all           # Verify all checks pass

# Run CLI during development
uv run protocol-codegen --help
```

### Code Quality Standards

All code must pass:
- ✅ **Ruff** - Zero linting errors, formatted code
- ✅ **Pyright** - Zero type errors in strict mode
- ✅ **Imports** - Sorted and organized

## License

MIT License - See LICENSE file

## Contact

- GitHub: [@petitechose-audio](https://github.com/petitechose-audio)
- Issues: [GitHub Issues](https://github.com/petitechose-audio/protocol-codegen/issues)
