# Protocol CodeGen

Generate type-safe protocol code (C++, Java) from Python message definitions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked with pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

## Features

- **Dual protocol support** - Serial8 (8-bit binary) and SysEx (7-bit MIDI)
- **Type-safe** - Compile-time error detection in C++ and Java
- **Cross-platform** - Identical C++ ↔ Java code generation
- **Optimized types** - `norm8`/`norm16` for bandwidth-efficient floats
- **Zero-allocation** - Streaming encoder pattern for Java
- **Auto ID allocation** - Sequential message IDs
- **Incremental generation** - Only regenerates changed files

## Protocol Methods

| Method | Encoding | Use Case | Bandwidth |
|--------|----------|----------|-----------|
| **serial8** | 8-bit binary | USB Serial + Bridge | High (full byte range) |
| **sysex** | 7-bit MIDI | Direct MIDI SysEx | Lower (7-bit constraint) |

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
git clone https://github.com/open-control/protocol-codegen.git
cd protocol-codegen

# Install dependencies and package
uv sync
```

## Quick Start

```bash
# Generate Serial8 protocol from example
cd examples/simple-sensor-network
protocol-codegen generate \
    --method serial8 \
    --messages message \
    --config protocol_config_serial8.py \
    --plugin-paths plugin_paths.py \
    --output-base . \
    --verbose
```

## Define Messages

### 1. Define Fields

**field/sensor.py:**
```python
from protocol_codegen.core.field import PrimitiveField, Type

sensor_id = PrimitiveField('sensorId', type_name=Type.UINT8)
sensor_value = PrimitiveField('value', type_name=Type.FLOAT32)
sensor_normalized = PrimitiveField('level', type_name=Type.NORM8)  # 0.0-1.0 in 1 byte
```

### 2. Define Messages

**message/sensor.py:**
```python
from protocol_codegen.core.message import Message
from field.sensor import *

SENSOR_READING = Message(
    description='Single sensor reading',
    fields=[sensor_id, sensor_value, sensor_normalized]
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

## Builtin Types

| Type | Size | C++ Type | Java Type | Description |
|------|------|----------|-----------|-------------|
| `bool` | 1 | `bool` | `boolean` | True/false |
| `uint8` | 1 | `uint8_t` | `int` | Unsigned 8-bit |
| `uint16` | 2 | `uint16_t` | `int` | Unsigned 16-bit |
| `uint32` | 4 | `uint32_t` | `long` | Unsigned 32-bit |
| `int8` | 1 | `int8_t` | `byte` | Signed 8-bit |
| `int16` | 2 | `int16_t` | `short` | Signed 16-bit |
| `int32` | 4 | `int32_t` | `int` | Signed 32-bit |
| `float32` | 4 | `float` | `float` | IEEE 754 float |
| `norm8` | 1 | `float` | `float` | Normalized 0.0-1.0 (7-bit) |
| `norm16` | 2 | `float` | `float` | Normalized 0.0-1.0 (16-bit) |
| `string` | var | `std::string` | `String` | UTF-8 with length prefix |

### Optimized Float Types

`norm8` and `norm16` are bandwidth-efficient alternatives to `float32` for normalized values:

```python
# Instead of float32 (4 bytes per value)
parameter_value = PrimitiveField('value', type_name=Type.FLOAT32)

# Use norm8 for UI values (1 byte, ~0.8% precision)
parameter_value = PrimitiveField('value', type_name=Type.NORM8)

# Use norm16 for higher precision (2 bytes)
parameter_value = PrimitiveField('value', type_name=Type.NORM16)
```

## Configuration

### Serial8 Configuration

**protocol_config.py:**
```python
from protocol_codegen.methods.serial8 import Serial8Config, Serial8Limits, Serial8Structure

PROTOCOL_CONFIG = Serial8Config(
    structure=Serial8Structure(
        message_type_offset=0,  # MessageID at byte 0
        from_host_offset=1,     # Direction flag at byte 1
        payload_offset=2,       # Payload starts at byte 2
    ),
    limits=Serial8Limits(
        string_max_length=32,
        array_max_items=32,
        max_payload_size=4096,
        max_message_size=4096,
    ),
)
```

### SysEx Configuration

**protocol_config.py:**
```python
from protocol_codegen.methods.sysex import SysExConfig, SysExLimits, SysExFraming

PROTOCOL_CONFIG = SysExConfig(
    framing=SysExFraming(
        manufacturer_id=0x7D,  # Educational use
        device_id=0x42,
    ),
    limits=SysExLimits(
        max_message_size=512,
        string_max_length=32,
    ),
)
```

### Output Paths

**plugin_paths.py:**
```python
PLUGIN_PATHS = {
    'output_cpp': {
        'base_path': 'generated/cpp',
        'namespace': 'Protocol',
        'structs': 'struct/',
    },
    'output_java': {
        'base_path': 'generated/java',
        'package': 'com.example.protocol',
        'structs': 'struct/',
    },
}
```

## Generate Code

```bash
# Serial8 protocol (recommended for high-bandwidth)
protocol-codegen generate \
    --method serial8 \
    --messages message \
    --config protocol_config.py \
    --plugin-paths plugin_paths.py \
    --output-base . \
    --verbose

# SysEx protocol (for MIDI-based systems)
protocol-codegen generate \
    --method sysex \
    --messages message \
    --config protocol_config.py \
    --plugin-paths plugin_paths.py \
    --output-base . \
    --verbose
```

## Generated Files

### C++ Output

```
generated/cpp/
├── Encoder.hpp           # Type → bytes encoding
├── Decoder.hpp           # Bytes → type decoding
├── Logger.hpp            # Debug logging helpers
├── MessageID.hpp         # Message ID enum
├── MessageStructure.hpp  # Message metadata
├── ProtocolConstants.hpp # Protocol limits
├── ProtocolCallbacks.hpp # Handler interface
├── DecoderRegistry.hpp   # Message routing
├── Protocol.hpp.template # Protocol implementation template
└── struct/
    ├── SensorReadingMessage.hpp
    └── ...
```

### Java Output

```
generated/java/com/example/protocol/
├── Encoder.java
├── Decoder.java
├── MessageID.java
├── ProtocolConstants.java
├── ProtocolCallbacks.java
├── DecoderRegistry.java
├── Protocol.java.template
└── struct/
    ├── SensorReadingMessage.java
    └── ...
```

## Use Generated Code

### C++

```cpp
#include "Encoder.hpp"
#include "struct/SensorReadingMessage.hpp"

SensorReadingMessage msg;
msg.sensorId = 1;
msg.value = 23.5f;
msg.level = 0.75f;  // norm8: stored as single byte

uint8_t buffer[64];
size_t len = Protocol::Encoder::encode(msg, buffer);
serial.write(buffer, len);
```

### Java (Streaming Encoder)

```java
import Encoder;
import struct.SensorReadingMessage;

SensorReadingMessage msg = new SensorReadingMessage();
msg.sensorId = 1;
msg.value = 23.5f;
msg.level = 0.75f;

// Zero-allocation streaming encode
byte[] buffer = new byte[64];
int len = Encoder.encode(msg, buffer, 0);
transport.send(buffer, 0, len);
```

## CLI Commands

```bash
# Generate protocol code
protocol-codegen generate --method serial8 --messages ... --config ... --plugin-paths ... --output-base .

# Validate messages without generating
protocol-codegen validate --method serial8 --messages message --verbose

# List available protocol methods
protocol-codegen list-methods

# List available code generators
protocol-codegen list-generators
```

## Architecture

```
src/protocol_codegen/
├── core/                    # Core abstractions
│   ├── field.py             # PrimitiveField, CompositeField
│   ├── message.py           # Message definition
│   ├── types.py             # Builtin type definitions
│   ├── allocator.py         # Message ID allocation
│   ├── validator.py         # Message validation
│   └── loader.py            # Type registry
├── methods/                 # Protocol methods
│   ├── serial8/             # 8-bit binary protocol
│   │   ├── config.py        # Serial8Config
│   │   └── generator.py     # Orchestrator
│   └── sysex/               # 7-bit MIDI protocol
│       ├── config.py        # SysExConfig
│       └── generator.py     # Orchestrator
└── generators/              # Code generators (by method)
    ├── serial8/
    │   ├── cpp/             # C++ generators
    │   └── java/            # Java generators
    └── sysex/
        ├── cpp/
        └── java/
```

## Examples

See `examples/simple-sensor-network/` for a complete example with:
- 10+ messages with various field types
- Nested composite types
- Arrays (fixed and dynamic)
- Both Serial8 and SysEx generation
- Full C++ and Java output

## Development

### Setup Development Environment

```bash
# Install package with development dependencies
uv sync --extra dev

# Verify installation
make all
```

### Available Commands

```bash
make help          # Show all available commands
make sync          # Sync all dependencies (including dev)
make format        # Format code with ruff
make lint          # Lint code with ruff
make type-check    # Type check with pyright
make all           # Run format, lint, type-check
make test          # Run tests with pytest
make example       # Run example generation
make clean         # Clean build artifacts
```

### Code Quality Standards

All code must pass:
- ✅ **Ruff** - Zero linting errors, formatted code
- ✅ **Pyright** - Zero type errors in strict mode
- ✅ **pytest** - All tests passing

## License

MIT License - See LICENSE file

## Related Projects

- [open-control/framework](https://github.com/open-control/framework) - Embedded controller framework (C++)
- [open-control/bridge](https://github.com/open-control/bridge) - Serial-to-UDP bridge for high-bandwidth communication (Rust)
