from field.color import color_rgb
from field.enums import AlertLevel, SensorCapabilities, SensorType
from protocol_codegen.core.field import CompositeField, EnumField, PrimitiveField, Type

# ============================================================================
# SENSOR FIELDS - Primitive types (FULL TYPE COVERAGE)
# ============================================================================

# --- Boolean ---
sensor_is_active = PrimitiveField("isActive", type_name=Type.BOOL)
sensor_is_error = PrimitiveField("hasError", type_name=Type.BOOL)

# --- Unsigned integers ---
sensor_id = PrimitiveField("sensorId", type_name=Type.UINT8)
sensor_battery_level = PrimitiveField("batteryLevel", type_name=Type.UINT8)  # 0-100%
sensor_update_interval = PrimitiveField("updateInterval", type_name=Type.UINT16)  # milliseconds
sensor_timestamp = PrimitiveField("timestamp", type_name=Type.UINT32)  # Unix timestamp

# --- Signed integers (ADDED: int16, int32) ---
sensor_temperature_raw = PrimitiveField(
    "temperatureRaw", type_name=Type.INT16
)  # Raw ADC value (-32768 to 32767)
sensor_calibration_offset = PrimitiveField(
    "calibrationOffset", type_name=Type.INT32
)  # High-precision offset

# --- Floating point ---
sensor_value = PrimitiveField("value", type_name=Type.FLOAT32)
sensor_threshold_min = PrimitiveField("thresholdMin", type_name=Type.FLOAT32)
sensor_threshold_max = PrimitiveField("thresholdMax", type_name=Type.FLOAT32)

# --- Normalized floats (ADDED: norm8, norm16) ---
# norm8: 0.0-1.0 stored in 1 byte (~0.8% precision) - ideal for UI/display
sensor_level = PrimitiveField("level", type_name=Type.NORM8)  # Visual indicator level
# norm16: 0.0-1.0 stored in 2 bytes (~0.003% precision) - for precise control
sensor_position = PrimitiveField("position", type_name=Type.NORM16)  # Precise position

# --- String ---
sensor_name = PrimitiveField("sensorName", type_name=Type.STRING)

# --- Visual representation ---
sensor_color = color_rgb  # Color indicator for sensor

# ============================================================================
# ENUM FIELDS (ADDED: EnumField with EnumDef)
# ============================================================================

# Basic enum usage
sensor_type_enum = EnumField("sensorType", enum_def=SensorType)

# Enum with string_mapping (generates fromString() in Java)
sensor_alert_level = EnumField("alertLevel", enum_def=AlertLevel)

# Bitflags enum (combinable with OR)
sensor_capabilities = EnumField("capabilities", enum_def=SensorCapabilities)

# ============================================================================
# COMPOSITE FIELDS - Nested structures
# ============================================================================

# SensorReading: Single sensor reading with metadata
# Demonstrates: basic composite with primitives
sensor_reading = [
    sensor_id,  # Which sensor (uint8)
    sensor_value,  # Reading value (float32)
    sensor_timestamp,  # When was it read (uint32)
    sensor_is_error,  # Was there an error? (bool)
]

# SensorInfo: Complete sensor information
# Demonstrates: composite with enums and various types
sensor_info = [
    sensor_id,  # Sensor identifier (uint8)
    sensor_name,  # Sensor name (string)
    sensor_type_enum,  # Sensor type (enum - replaces uint8)
    sensor_color,  # Display color (uint32 RGB)
    sensor_is_active,  # Is sensor active? (bool)
    sensor_battery_level,  # Battery level 0-100 (uint8)
    sensor_update_interval,  # Update rate in ms (uint16)
    sensor_capabilities,  # Bitflags capabilities (enum/uint8)
]

# SensorConfig: Configuration for a sensor
# Demonstrates: composite with signed types and floats
sensor_config = [
    sensor_id,  # Which sensor to configure (uint8)
    sensor_update_interval,  # Update interval (uint16)
    sensor_threshold_min,  # Minimum threshold (float32)
    sensor_threshold_max,  # Maximum threshold (float32)
    sensor_calibration_offset,  # Calibration offset (int32 - ADDED)
]

# CalibrationData: Sensor calibration info
# Demonstrates: using int16, norm8, norm16
calibration_data = [
    sensor_id,  # Which sensor (uint8)
    sensor_temperature_raw,  # Raw ADC value (int16)
    sensor_level,  # Visual level (norm8 - 0.0-1.0)
    sensor_position,  # Precise position (norm16 - 0.0-1.0)
]

# ============================================================================
# COMPOSITE FIELD ARRAYS - Collections
# ============================================================================

# --- Fixed-size arrays (std::array in C++) ---

# Array of sensor readings (max 8 sensors)
# Use case: Batch send multiple sensor values
sensor_readings_array = CompositeField("readings", fields=sensor_reading, array=8)

# Array of sensor info (max 16 sensors in network)
# Use case: Send full sensor list to controller
sensor_info_array = CompositeField("sensors", fields=sensor_info, array=16)

# --- Dynamic arrays (ADDED: std::vector in C++) ---
# Note: dynamic=True is only supported for PrimitiveField, not CompositeField

# Dynamic array of sensor IDs (variable size, max 64)
# Use case: List of active sensor IDs
# Generated as std::vector<uint8_t> in C++
sensor_ids_dynamic = PrimitiveField("sensorIds", type_name=Type.UINT8, array=64, dynamic=True)

# Dynamic array of float values (variable size, max 128)
# Use case: Time series data
# Generated as std::vector<float> in C++
values_dynamic = PrimitiveField("values", type_name=Type.FLOAT32, array=128, dynamic=True)

# Dynamic array of normalized values (variable size, max 32)
# Use case: Calibration levels
# Generated as std::vector<float> in C++ (norm8 exposed as float)
levels_dynamic = PrimitiveField("levels", type_name=Type.NORM8, array=32, dynamic=True)
