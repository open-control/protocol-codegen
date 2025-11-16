# Protocol CodeGen - Examples

This directory contains example protocols demonstrating different features and complexity levels.

## Available Examples

### 📁 simple-sensor-network/

**Status:** ✅ Complete (waiting for Phase 2 to test)

**What it demonstrates:**
- Primitive fields (UINT8, FLOAT32, STRING, etc.)
- Composite fields (groups of primitives)
- Composite field arrays (arrays of structs)
- Nested composites (composites referencing other composites)
- 10 messages from simple (3 bytes) to complex (650 bytes)

**Complexity:**
- ⭐ Beginner-friendly structure
- ⭐⭐ Shows best practices for field organization
- ⭐⭐⭐ Demonstrates memory considerations

**Use case:** IoT sensor network with Arduino/Teensy ↔ Desktop host

**Documentation:**
- `README.md` - Complete guide
- `STRUCTURE.txt` - Visual type hierarchy
- `MESSAGES.md` - Message reference with sizes

---

## Comparison with Real Projects

### simple-sensor-network vs plugin/bitwig

Both use the same architecture pattern:

| Aspect | simple-sensor-network | plugin/bitwig |
|--------|----------------------|---------------|
| **Structure** | field/ + message/ | field/ + message/ |
| **Primitive fields** | color.py, sensor.py, network.py | color.py, parameter.py, track.py, transport.py |
| **Composites** | sensor_reading, sensor_info | track_info, parameter fields |
| **Arrays** | sensor_readings_array[8], sensor_info_array[16] | track_list[32] |
| **Messages** | 10 messages | ~25 messages |
| **Nesting** | color_rgb → sensor_info → sensor_info_array | color_rgb → track_info → track_list |

**Key difference:** Bitwig is production-ready, sensor-network is a learning example.

---

## Complexity Levels

### Level 1: Simple Message (no composites)
```python
# Example: SENSOR_READING_SINGLE
MESSAGE = Message(
    fields=[
        primitive_field1,  # UINT8
        primitive_field2,  # FLOAT32
        primitive_field3   # UINT32
    ]
)
```

### Level 2: Array Message
```python
# Example: SENSOR_READING_BATCH
MESSAGE = Message(
    fields=[
        CompositeField('items', fields=[...], array=8)
    ]
)
```

### Level 3: Nested Composites
```python
# Example: SENSOR_LIST
color = PrimitiveField('color', Type.UINT32)  # Level 1

sensor_info = [                                # Level 2 (uses color)
    sensor_id,
    color,  # ← nested
    sensor_name
]

sensor_list = CompositeField(                  # Level 3 (uses sensor_info)
    'sensors',
    fields=sensor_info,
    array=16
)

MESSAGE = Message(                             # Level 4 (uses sensor_list)
    fields=[sensor_list]
)
```

---

## Creating Your Own Example

### Step 1: Create Directory Structure
```bash
mkdir -p examples/my-protocol/{field,message}
touch examples/my-protocol/field/__init__.py
touch examples/my-protocol/message/__init__.py
```

### Step 2: Define Fields
```python
# examples/my-protocol/field/myfields.py
from protocol import PrimitiveField, CompositeField, Type

my_id = PrimitiveField('myId', type_name=Type.UINT8)
my_value = PrimitiveField('myValue', type_name=Type.FLOAT32)

# Composite
my_struct = [
    my_id,
    my_value
]

# Array of composites
my_array = CompositeField('items', fields=my_struct, array=10)
```

### Step 3: Define Messages
```python
# examples/my-protocol/message/mymessages.py
from protocol import Message
from ..field.myfields import *

MY_MESSAGE = Message(
    description='My custom message',
    fields=[my_id, my_value]
)

ALL_MESSAGES = [MY_MESSAGE]
```

### Step 4: Configuration
```python
# examples/my-protocol/protocol_config.py
from protocol_codegen.methods.sysex import SysExConfig, SysExLimits

PROTOCOL_CONFIG = SysExConfig(
    manufacturer_id=0x7D,  # Educational use
    device_id=0x01,
    limits=SysExLimits(
        max_message_size=512,
        string_max_length=32,
        array_max_size=32
    )
)
```

---

## Testing Your Example

Once Phase 2 is complete:

```bash
# Generate code
protocol-codegen generate \
  --method sysex \
  --messages examples/my-protocol/message/__init__.py \
  --config examples/my-protocol/protocol_config.py \
  --output-cpp examples/my-protocol/generated/cpp \
  --output-java examples/my-protocol/generated/java

# Check generated files
ls examples/my-protocol/generated/cpp/
ls examples/my-protocol/generated/java/
```

---

## Best Practices

### Organization
✅ **DO:** Separate fields by category (field/color.py, field/sensor.py)  
✅ **DO:** Keep composites in the same file as their primitives  
✅ **DO:** Document field sizes and memory impact  
❌ **DON'T:** Mix unrelated fields in one file  
❌ **DON'T:** Create huge arrays without considering SysEx size limits

### Naming
✅ **DO:** Use clear, descriptive names (sensor_is_active, not sia)  
✅ **DO:** Use snake_case for fields  
✅ **DO:** Use SCREAMING_SNAKE_CASE for messages  
❌ **DON'T:** Use abbreviations unless very common (id, rgb ok, val not ok)

### Memory
✅ **DO:** Calculate message sizes (see MESSAGES.md)  
✅ **DO:** Keep arrays small (<32 elements typically)  
✅ **DO:** Limit string lengths (32 chars max recommended)  
❌ **DON'T:** Create messages >512 bytes raw (~900 bytes SysEx)  
❌ **DON'T:** Use unlimited arrays

---

## Future Examples (Planned)

### sysex-arduino-python/
Simple Arduino sketch + Python host demonstrating basic communication.

### sysex-teensy-java/
Teensy 4.1 + Java desktop app (similar to Bitwig but simplified).

### osc-cpp-js/ (when OSC support added)
OSC protocol example for audio applications.

---

**Status:** simple-sensor-network complete, others pending Phase 2+
**Last updated:** 2024-11-16
