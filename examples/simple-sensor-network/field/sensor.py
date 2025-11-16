from protocol_codegen.core.field import PrimitiveField, CompositeField, Type
from field.color import color_rgb

# ============================================================================
# SENSOR FIELDS - Primitive types
# ============================================================================

# Sensor identification
sensor_id = PrimitiveField('sensorId', type_name=Type.UINT8)
sensor_name = PrimitiveField('sensorName', type_name=Type.STRING)
sensor_type = PrimitiveField('sensorType', type_name=Type.UINT8)  # 0=temp, 1=humidity, 2=pressure

# Sensor status
sensor_is_active = PrimitiveField('isActive', type_name=Type.BOOL)
sensor_is_error = PrimitiveField('hasError', type_name=Type.BOOL)
sensor_battery_level = PrimitiveField('batteryLevel', type_name=Type.UINT8)  # 0-100%

# Sensor readings
sensor_value = PrimitiveField('value', type_name=Type.FLOAT32)
sensor_timestamp = PrimitiveField('timestamp', type_name=Type.UINT32)  # Unix timestamp

# Sensor configuration
sensor_update_interval = PrimitiveField('updateInterval', type_name=Type.UINT16)  # milliseconds
sensor_threshold_min = PrimitiveField('thresholdMin', type_name=Type.FLOAT32)
sensor_threshold_max = PrimitiveField('thresholdMax', type_name=Type.FLOAT32)

# Visual representation
sensor_color = color_rgb  # Color indicator for sensor

# ============================================================================
# COMPOSITE FIELDS - Nested structures
# ============================================================================

# SensorReading: Single sensor reading with metadata
sensor_reading = [
    sensor_id,              # Which sensor (uint8)
    sensor_value,           # Reading value (float32)
    sensor_timestamp,       # When was it read (uint32)
    sensor_is_error         # Was there an error? (bool)
]

# SensorInfo: Complete sensor information
sensor_info = [
    sensor_id,              # Sensor identifier (uint8)
    sensor_name,            # Sensor name (string)
    sensor_type,            # Sensor type (uint8)
    sensor_color,           # Display color (uint32 RGB)
    sensor_is_active,       # Is sensor active? (bool)
    sensor_battery_level,   # Battery level 0-100 (uint8)
    sensor_update_interval  # Update rate in ms (uint16)
]

# SensorConfig: Configuration for a sensor
sensor_config = [
    sensor_id,              # Which sensor to configure (uint8)
    sensor_update_interval, # Update interval (uint16)
    sensor_threshold_min,   # Minimum threshold (float32)
    sensor_threshold_max    # Maximum threshold (float32)
]

# ============================================================================
# COMPOSITE FIELD ARRAYS - Collections
# ============================================================================

# Array of sensor readings (max 8 sensors)
# Use case: Batch send multiple sensor values
sensor_readings_array = CompositeField('readings', fields=sensor_reading, array=8)

# Array of sensor info (max 16 sensors in network)
# Use case: Send full sensor list to controller
sensor_info_array = CompositeField('sensors', fields=sensor_info, array=16)
