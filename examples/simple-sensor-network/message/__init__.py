# Import all messages to make them available to protocol generator
from .sensor import *
from .network import *

# All messages list for generator
ALL_MESSAGES = [
    # Sensor messages
    SENSOR_READING_SINGLE,
    SENSOR_READING_BATCH,
    REQUEST_SENSOR_LIST,
    SENSOR_LIST,
    SENSOR_CONFIG_SET,
    SENSOR_CONFIG_GET,
    SENSOR_ACTIVATE,
    SENSOR_DEACTIVATE,

    # Network messages
    NETWORK_STATUS,
    REQUEST_NETWORK_STATUS,
]

# Auto-inject message names from variable names
_message_map = {
    'SENSOR_READING_SINGLE': SENSOR_READING_SINGLE,
    'SENSOR_READING_BATCH': SENSOR_READING_BATCH,
    'REQUEST_SENSOR_LIST': REQUEST_SENSOR_LIST,
    'SENSOR_LIST': SENSOR_LIST,
    'SENSOR_CONFIG_SET': SENSOR_CONFIG_SET,
    'SENSOR_CONFIG_GET': SENSOR_CONFIG_GET,
    'SENSOR_ACTIVATE': SENSOR_ACTIVATE,
    'SENSOR_DEACTIVATE': SENSOR_DEACTIVATE,
    'NETWORK_STATUS': NETWORK_STATUS,
    'REQUEST_NETWORK_STATUS': REQUEST_NETWORK_STATUS,
}

for name, message in _message_map.items():
    message.name = name
