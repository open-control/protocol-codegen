from protocol_codegen.core.field import PrimitiveField, Type

# ============================================================================
# NETWORK FIELDS
# ============================================================================

# Network identification
network_id = PrimitiveField('networkId', type_name=Type.UINT16)
network_name = PrimitiveField('networkName', type_name=Type.STRING)

# Network statistics
sensor_count = PrimitiveField('sensorCount', type_name=Type.UINT8)
active_sensor_count = PrimitiveField('activeSensorCount', type_name=Type.UINT8)

# Network status
network_is_online = PrimitiveField('isOnline', type_name=Type.BOOL)
network_rssi = PrimitiveField('rssi', type_name=Type.INT8)  # Signal strength in dBm
