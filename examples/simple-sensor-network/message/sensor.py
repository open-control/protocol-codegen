from field.network import sensor_count
from field.sensor import (
    levels_dynamic,
    sensor_alert_level,
    sensor_calibration_offset,
    sensor_capabilities,
    sensor_id,
    sensor_ids_dynamic,
    sensor_info_array,
    sensor_level,
    sensor_position,
    sensor_readings_array,
    sensor_temperature_raw,
    sensor_threshold_max,
    sensor_threshold_min,
    sensor_timestamp,
    sensor_type_enum,
    sensor_update_interval,
    sensor_value,
    values_dynamic,
)

from protocol_codegen.core.message import Message

# ============================================================================
# SENSOR READING MESSAGES
# ============================================================================

# Device → Host: Single sensor reading (simple message)
SENSOR_READING_SINGLE = Message(
    description="Single sensor reading with timestamp",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_value,  # FLOAT32 - Reading value
        sensor_timestamp,  # UINT32 - When
    ],
)

# Device → Host: Batch sensor readings (uses composite field array)
SENSOR_READING_BATCH = Message(
    description="Batch of sensor readings (up to 8 sensors)",
    fields=[
        sensor_readings_array  # CompositeField array of SensorReading structs
    ],
)

# ============================================================================
# SENSOR DISCOVERY & INFO MESSAGES
# ============================================================================

# Host → Device: Request list of sensors
REQUEST_SENSOR_LIST = Message(
    description="Request list of all sensors in network",
    fields=[],  # No parameters needed
)

# Device → Host: Complete sensor list (uses composite field array with enums)
SENSOR_LIST = Message(
    description="List of all sensors with complete info",
    fields=[
        sensor_count,  # UINT8 - Total sensors
        sensor_info_array,  # CompositeField array with SensorType enum & capabilities bitflags
    ],
)

# ============================================================================
# SENSOR CONFIGURATION MESSAGES
# ============================================================================

# Host → Device: Set sensor configuration (with int32 calibration offset)
SENSOR_CONFIG_SET = Message(
    description="Configure sensor thresholds, interval and calibration",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_update_interval,  # UINT16 - Update interval (ms)
        sensor_threshold_min,  # FLOAT32 - Min threshold
        sensor_threshold_max,  # FLOAT32 - Max threshold
        sensor_calibration_offset,  # INT32 - Calibration offset (ADDED)
    ],
)

# Host → Device: Get sensor configuration
SENSOR_CONFIG_GET = Message(
    description="Request sensor configuration",
    fields=[
        sensor_id  # UINT8 - Which sensor
    ],
)

# ============================================================================
# SENSOR CONTROL MESSAGES
# ============================================================================

# Host → Device: Activate sensor
SENSOR_ACTIVATE = Message(
    description="Activate a sensor",
    fields=[
        sensor_id  # UINT8 - Which sensor to activate
    ],
)

# Host → Device: Deactivate sensor
SENSOR_DEACTIVATE = Message(
    description="Deactivate a sensor",
    fields=[
        sensor_id  # UINT8 - Which sensor to deactivate
    ],
)

# ============================================================================
# NEW MESSAGES - Demonstrating additional features
# ============================================================================

# --- Enum features ---

# Device → Host: Sensor alert (uses AlertLevel enum with string_mapping)
SENSOR_ALERT = Message(
    description="Sensor alert notification with severity level",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_alert_level,  # AlertLevel enum (with string_mapping for fromString())
        sensor_value,  # FLOAT32 - Current value that triggered alert
        sensor_timestamp,  # UINT32 - When alert occurred
    ],
)

# Host → Device: Query sensor type (uses SensorType enum)
SENSOR_TYPE_QUERY = Message(
    description="Query or set sensor type classification",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_type_enum,  # SensorType enum (basic enum)
    ],
)

# Device → Host: Report sensor capabilities (uses bitflags enum)
SENSOR_CAPABILITIES_REPORT = Message(
    description="Report sensor capabilities (combinable bitflags)",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_capabilities,  # SensorCapabilities bitflags (CAN_READ | CAN_CONFIGURE, etc.)
    ],
)

# --- Signed integer features ---

# Device → Host: Raw sensor reading with int16
SENSOR_RAW_READING = Message(
    description="Raw ADC reading from sensor (signed 16-bit)",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_temperature_raw,  # INT16 - Raw ADC value (-32768 to 32767)
        sensor_timestamp,  # UINT32 - When
    ],
)

# --- Normalized float features ---

# Device → Host: Sensor level update (uses norm8/norm16)
SENSOR_LEVEL_UPDATE = Message(
    description="Sensor level update using normalized floats",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_level,  # NORM8 - Visual level (0.0-1.0 in 1 byte)
        sensor_position,  # NORM16 - Precise position (0.0-1.0 in 2 bytes)
    ],
)

# --- Dynamic array features ---

# Device → Host: Calibration levels batch (dynamic norm8 array)
CALIBRATION_LEVELS = Message(
    description="Batch calibration levels (variable size norm8 array)",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        levels_dynamic,  # Dynamic NORM8 array (std::vector<float> in C++)
    ],
)

# Host → Device: Set active sensors (dynamic primitive array)
SET_ACTIVE_SENSORS = Message(
    description="Set list of active sensor IDs (variable size)",
    fields=[
        sensor_ids_dynamic,  # Dynamic UINT8 array (std::vector<uint8_t> in C++)
    ],
)

# Device → Host: Time series data (dynamic float array)
SENSOR_TIME_SERIES = Message(
    description="Time series sensor data (variable size float array)",
    fields=[
        sensor_id,  # UINT8 - Which sensor
        sensor_timestamp,  # UINT32 - Start time
        values_dynamic,  # Dynamic FLOAT32 array (std::vector<float> in C++)
    ],
)
