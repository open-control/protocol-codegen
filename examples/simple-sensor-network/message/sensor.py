from protocol_codegen.core.message import Message
from protocol_codegen.core.field import PrimitiveField, CompositeField, Type
from field.sensor import *
from field.network import sensor_count

# ============================================================================
# SENSOR READING MESSAGES
# ============================================================================

# Device → Host: Single sensor reading (simple message)
SENSOR_READING_SINGLE = Message(
    description='Single sensor reading with timestamp',
    fields=[
        sensor_id,          # UINT8 - Which sensor
        sensor_value,       # FLOAT32 - Reading value
        sensor_timestamp    # UINT32 - When
    ]
)

# Device → Host: Batch sensor readings (uses composite field array)
SENSOR_READING_BATCH = Message(
    description='Batch of sensor readings (up to 8 sensors)',
    fields=[
        sensor_readings_array  # CompositeField array of SensorReading structs
    ]
)

# ============================================================================
# SENSOR DISCOVERY & INFO MESSAGES
# ============================================================================

# Host → Device: Request list of sensors
REQUEST_SENSOR_LIST = Message(
    description='Request list of all sensors in network',
    fields=[]  # No parameters needed
)

# Device → Host: Complete sensor list (uses composite field array)
SENSOR_LIST = Message(
    description='List of all sensors with complete info',
    fields=[
        sensor_count,       # UINT8 - Total sensors
        sensor_info_array   # CompositeField array of SensorInfo structs (max 16)
    ]
)

# ============================================================================
# SENSOR CONFIGURATION MESSAGES
# ============================================================================

# Host → Device: Set sensor configuration
SENSOR_CONFIG_SET = Message(
    description='Configure sensor thresholds and update interval',
    fields=[
        sensor_id,              # UINT8 - Which sensor
        sensor_update_interval, # UINT16 - Update interval (ms)
        sensor_threshold_min,   # FLOAT32 - Min threshold
        sensor_threshold_max    # FLOAT32 - Max threshold
    ]
)

# Host → Device: Get sensor configuration
SENSOR_CONFIG_GET = Message(
    description='Request sensor configuration',
    fields=[
        sensor_id  # UINT8 - Which sensor
    ]
)

# ============================================================================
# SENSOR CONTROL MESSAGES
# ============================================================================

# Host → Device: Activate sensor
SENSOR_ACTIVATE = Message(
    description='Activate a sensor',
    fields=[
        sensor_id  # UINT8 - Which sensor to activate
    ]
)

# Host → Device: Deactivate sensor
SENSOR_DEACTIVATE = Message(
    description='Deactivate a sensor',
    fields=[
        sensor_id  # UINT8 - Which sensor to deactivate
    ]
)
