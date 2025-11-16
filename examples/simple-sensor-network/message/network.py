from protocol_codegen.core.message import Message
from protocol_codegen.core.field import PrimitiveField, CompositeField, Type
from field.network import *

# ============================================================================
# NETWORK STATUS MESSAGES
# ============================================================================

# Device → Host: Network status update
NETWORK_STATUS = Message(
    description='Network status information',
    fields=[
        network_id,             # UINT16 - Network identifier
        network_name,           # STRING - Network name
        sensor_count,           # UINT8 - Total sensors
        active_sensor_count,    # UINT8 - Active sensors
        network_is_online,      # BOOL - Network online
        network_rssi            # INT8 - Signal strength (dBm)
    ]
)

# Host → Device: Request network status
REQUEST_NETWORK_STATUS = Message(
    description='Request current network status',
    fields=[]  # No parameters
)
