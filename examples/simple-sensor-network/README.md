# Simple Sensor Network Example

Demonstrates protocol-codegen with nested composite types for a sensor network.

## Quick Start

```bash
# Install protocol-codegen (from project root)
cd ../..
uv sync

# Generate code
cd examples/simple-sensor-network
./generate.sh  # or generate.bat on Windows
```

## Structure

```
simple-sensor-network/
├── field/              # Field definitions (types)
│   ├── color.py
│   ├── sensor.py
│   └── network.py
├── message/            # Message definitions
│   ├── sensor.py
│   ├── network.py
│   └── __init__.py
├── protocol_config.py  # SysEx configuration
├── plugin_paths.py     # Output paths
├── generate.sh         # Generation script
└── generated/          # Generated C++ and Java code
```

## Generated Output

**C++ (generated/cpp/):**
- Encoder.hpp, Decoder.hpp, Logger.hpp
- ProtocolConstants.hpp, MessageID.hpp
- struct/ - 10 message structs

**Java (generated/java/):**
- Encoder.java, Decoder.java
- ProtocolConstants.java, MessageID.java
- struct/ - 10 message classes

## Configuration

### Protocol Settings (`protocol_config.py`)

Configure SysEx framing and limits:
```python
PROTOCOL_CONFIG = SysExConfig(
    framing=SysExFraming(
        manufacturer_id=0x7D,  # Educational use
        device_id=0x42,
    ),
    limits=SysExLimits(
        max_message_size=512,
        string_max_length=32,
        array_max_items=32
    )
)
```

### Output Paths (`plugin_paths.py`)

Simplified configuration - language-specific settings stay with their language:

```python
PLUGIN_PATHS = {
    "output_cpp": {
        "base_path": "generated/cpp",
        "namespace": "SensorProtocol",  # C++ namespace
        "structs": "struct/",           # Relative to base_path
    },
    "output_java": {
        "base_path": "generated/java/com/example/sensor",
        "package": "com.example.sensor",  # Java package
        "structs": "struct/",             # Relative to base_path
    },
}
```

**Key points:**
- `namespace` and `package` live with their respective language config
- `structs` path is relative to `base_path` (no repetition)
- No TypedDict pollution - just a simple Python dict

## Messages

10 messages defined:
- SENSOR_READING_SINGLE - Single sensor value
- SENSOR_READING_BATCH - Batch readings (array)
- SENSOR_LIST - List of all sensors (nested composites)
- REQUEST_SENSOR_LIST - Query sensors
- SENSOR_CONFIG_SET/GET - Configure sensor
- SENSOR_ACTIVATE/DEACTIVATE - Control sensor
- NETWORK_STATUS - Network info
- REQUEST_NETWORK_STATUS - Query network

See `message/*.py` for details.
