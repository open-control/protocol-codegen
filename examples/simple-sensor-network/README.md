# Simple Sensor Network Example

Demonstrates protocol-codegen with nested composite types for a sensor network.

## Quick Start

```bash
# Install protocol-codegen (from project root)
pip install -e .

# Generate code
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

Edit `protocol_config.py`:
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
