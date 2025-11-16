# Protocol CodeGen

Generate type-safe protocol code (C++, Java) from Python message definitions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **SysEx protocol** - MIDI System Exclusive
- **Type-safe** - Compile-time error detection
- **Bidirectional** - C++ ↔ Java communication
- **Auto ID allocation** - Sequential message IDs
- **Validation** - Strict message validation

## Quick Start

```bash
# Install
pip install -e .

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
        'structs': 'generated/cpp/struct/',
    },
    'output_java': {
        'base_path': 'generated/java',
        'structs': 'generated/java/struct/',
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

```bash
# Install dev mode
pip install -e .

# Run example
cd examples/simple-sensor-network
./generate.sh
```

## License

MIT License - See LICENSE file

## Contact

- GitHub: [@petitechose-audio](https://github.com/petitechose-audio)
- Issues: [GitHub Issues](https://github.com/petitechose-audio/protocol-codegen/issues)
